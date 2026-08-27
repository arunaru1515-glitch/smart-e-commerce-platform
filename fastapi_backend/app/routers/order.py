from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.notification import Notification
from app.models.user import User
from app.core.security import get_current_user

from app.services.websocket_service import manager


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# =========================================================
# UPDATE ORDER STATUS - ADMIN ONLY
# =========================================================

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. CHECK ADMIN ACCESS
    # =====================================================

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can update order status"
        )


    # =====================================================
    # 2. FIND ORDER
    # =====================================================

    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    # =====================================================
    # 3. VALIDATE STATUS
    # =====================================================

    status = status.lower().strip()

    allowed_statuses = {
        "paid",
        "shipped",
        "delivered",
        "cancelled"
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use paid, shipped, delivered or cancelled."
            )
        )


    # =====================================================
    # 4. CHECK IF STATUS IS ALREADY SET
    # =====================================================

    if order.order_status == status:

        return {
            "message": "Order already has this status",
            "order_id": order.id,
            "order_status": order.order_status,
            "notification_id": None
        }


    # =====================================================
    # 5. UPDATE ORDER STATUS
    # =====================================================

    order.order_status = status


    # =====================================================
    # 6. UPDATE PAYMENT STATUS WHEN NECESSARY
    # =====================================================

    if status == "paid":
        order.payment_status = "paid"

    elif status == "cancelled":
        if order.payment_status != "paid":
            order.payment_status = "failed"


    # =====================================================
    # 7. CREATE CUSTOMER NOTIFICATION
    # =====================================================

    notification = None

    if status == "paid":

        notification = Notification(
            user=order.user,
            type="order_confirmed",
            message=(
                f"Your Order #{order.id} has been confirmed."
            ),
            read_status="unread"
        )

    elif status == "shipped":

        notification = Notification(
            user=order.user,
            type="order_shipped",
            message=(
                f"Your Order #{order.id} has been shipped."
            ),
            read_status="unread"
        )

    elif status == "delivered":

        notification = Notification(
            user=order.user,
            type="order_delivered",
            message=(
                f"Your Order #{order.id} has been delivered."
            ),
            read_status="unread"
        )

    elif status == "cancelled":

        notification = Notification(
            user=order.user,
            type="order_cancelled",
            message=(
                f"Your Order #{order.id} has been cancelled."
            ),
            read_status="unread"
        )


    # =====================================================
    # 8. SAVE CHANGES
    # =====================================================

    if notification:
        db.add(notification)

    try:

        db.commit()

        db.refresh(order)

        if notification:
            db.refresh(notification)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


    # =====================================================
    # 9. SEND REAL-TIME ORDER UPDATE
    # =====================================================

    await manager.send_to_user(
        order.user,
        {
            "event": "order_status_updated",
            "order_id": order.id,
            "order_status": order.order_status
        }
    )


    # =====================================================
    # 10. RESPONSE
    # =====================================================

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "notification_id": (
            notification.id
            if notification
            else None
        )
    }