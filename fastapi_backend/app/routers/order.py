from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.notification import Notification
from app.models.return_request import ReturnRequest
from app.models.user import User
from app.core.security import get_current_user

from app.services.websocket_service import manager
from app.services.email_service import send_order_status_email


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# =========================================================
# RETURN REQUEST SCHEMA
# =========================================================

class ReturnRequestCreate(BaseModel):
    reason: str
    comment: str | None = None


# =========================================================
# GET MY ORDERS - CUSTOMER
# =========================================================

@router.get("/")
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders belonging to the currently
    logged-in customer.
    """

    orders = (
        db.query(Order)
        .filter(Order.user == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return [
        {
            "id": order.id,
            "user_id": order.user,
            "products": order.products,
            "total": (
                float(order.total)
                if order.total is not None
                else 0
            ),
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "created_at": order.created_at,
            "delivered_at": order.delivered_at,
        }
        for order in orders
    ]


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

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

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
    # 6. SAVE DELIVERY DATE
    # =====================================================

    if status == "delivered":
        order.delivered_at = datetime.utcnow()


    # =====================================================
    # 7. UPDATE PAYMENT STATUS
    # =====================================================

    if status == "paid":

        order.payment_status = "paid"

    elif status == "cancelled":

        if order.payment_status != "paid":
            order.payment_status = "failed"


    # =====================================================
    # 8. CREATE CUSTOMER NOTIFICATION
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
    # 9. SAVE CHANGES
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
    # 10. GET CUSTOMER EMAIL
    # =====================================================

    customer = (
        db.query(User)
        .filter(User.id == order.user)
        .first()
    )


    # =====================================================
    # 11. SEND EMAIL FOR ORDER STATUS UPDATE
    # =====================================================

    email_sent = False


    if customer and customer.email:

        try:

            send_order_status_email(
                to_email=customer.email,
                order_id=order.id,
                status=status,
                products=order.products,
                total_amount=order.total
            )

            email_sent = True

            print(
                f"{status.upper()} email sent "
                f"for Order #{order.id}"
            )

        except Exception as e:

            # Email failure should not undo
            # the already successful order update.

            print(
                f"Order status email failed: {str(e)}"
            )


    # =====================================================
    # 12. SEND REAL-TIME ORDER UPDATE
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
    # 13. RESPONSE
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
        ),
        "email_sent": email_sent
    }


# =========================================================
# REQUEST RETURN - CUSTOMER
# =========================================================

@router.post("/{order_id}/return")
async def request_return(
    order_id: int,
    request: ReturnRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. FIND ORDER
    # =====================================================

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    # =====================================================
    # 2. CHECK ORDER OWNERSHIP
    # =====================================================

    if order.user != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="You are not allowed to return this order"
        )


    # =====================================================
    # 3. CHECK ORDER STATUS
    # =====================================================

    if order.order_status != "delivered":

        raise HTTPException(
            status_code=400,
            detail=(
                "Return can only be requested "
                "for delivered orders"
            )
        )


    # =====================================================
    # 4. CHECK DELIVERY DATE
    # =====================================================

    if not order.delivered_at:

        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery date is not available "
                "for this order"
            )
        )


    # =====================================================
    # 5. CHECK RETURN WINDOW - 7 DAYS
    # =====================================================

    delivered_at = order.delivered_at


    if delivered_at.tzinfo is None:

        delivered_at = delivered_at.replace(
            tzinfo=timezone.utc
        )


    current_time = datetime.now(
        timezone.utc
    )


    return_deadline = (
        delivered_at +
        timedelta(days=7)
    )


    if current_time > return_deadline:

        raise HTTPException(
            status_code=400,
            detail=(
                "Return window has expired. "
                "Returns are allowed within "
                "7 days of delivery."
            )
        )


    # =====================================================
    # 6. VALIDATE RETURN REASON
    # =====================================================

    reason = request.reason.strip()


    if not reason:

        raise HTTPException(
            status_code=400,
            detail="Return reason is required"
        )


    # =====================================================
    # 7. CHECK EXISTING RETURN REQUEST
    # =====================================================

    existing_request = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_id == order.id,
            ReturnRequest.user_id == current_user.id,
            ReturnRequest.status.in_(
                ["pending", "approved"]
            )
        )
        .first()
    )


    if existing_request:

        raise HTTPException(
            status_code=400,
            detail=(
                "A return request already exists "
                "for this order"
            )
        )


    # =====================================================
    # 8. CREATE RETURN REQUEST
    # =====================================================

    return_request = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=reason,
        comment=(
            request.comment.strip()
            if request.comment
            else None
        ),
        status="pending"
    )


    db.add(return_request)


    # =====================================================
    # 9. UPDATE ORDER STATUS
    # =====================================================

    order.order_status = "return_requested"


    # =====================================================
    # 10. CREATE CUSTOMER NOTIFICATION
    # =====================================================

    notification = Notification(
        user=order.user,
        type="return_requested",
        message=(
            f"Your return request for Order #{order.id} "
            f"has been submitted successfully."
        ),
        read_status="unread"
    )


    db.add(notification)


    # =====================================================
    # 11. SAVE DATABASE CHANGES
    # =====================================================

    try:

        db.commit()

        db.refresh(return_request)

        db.refresh(order)

        db.refresh(notification)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


    # =====================================================
    # 12. SEND REAL-TIME UPDATE
    # =====================================================

    await manager.send_to_user(
        order.user,
        {
            "event": "return_requested",
            "order_id": order.id,
            "order_status": order.order_status,
            "return_request_id": return_request.id
        }
    )


    # =====================================================
    # 13. RESPONSE
    # =====================================================

    return {
        "message": (
            "Return request submitted successfully"
        ),
        "return_request_id": return_request.id,
        "order_id": order.id,
        "order_status": order.order_status,
        "return_status": return_request.status,
        "reason": return_request.reason,
        "comment": return_request.comment,
        "created_at": return_request.created_at
    }