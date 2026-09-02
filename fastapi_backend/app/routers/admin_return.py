from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.stripe_service import create_refund

from app.services.email_service import send_email

from app.models.user import User
from app.models.return_request import ReturnRequest
from app.models.order import Order
from app.models.product import Product
from app.models.payment import Payment
from app.models.notification import Notification


router = APIRouter(
    prefix="/admin/returns",
    tags=["Admin Returns"]
)


# =========================================================
# GET ALL RETURN REQUESTS
# =========================================================

@router.get("")
def get_all_returns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # -----------------------------------------------------
    # ADMIN AUTHORIZATION
    # -----------------------------------------------------

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can view return requests"
        )

    # -----------------------------------------------------
    # GET ALL RETURNS
    # -----------------------------------------------------

    return_requests = (
        db.query(ReturnRequest)
        .order_by(ReturnRequest.created_at.desc())
        .all()
    )

    return [
        {
            "id": return_request.id,
            "order_id": return_request.order_id,
            "user_id": return_request.user_id,
            "reason": return_request.reason,
            "comment": return_request.comment,
            "status": return_request.status,
            "created_at": return_request.created_at
        }
        for return_request in return_requests
    ]


# =========================================================
# APPROVE RETURN
# INVENTORY + STRIPE REFUND + NOTIFICATIONS + EMAIL
# =========================================================

@router.post("/{return_id}/approve")
def approve_return(
    return_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # -----------------------------------------------------
    # ADMIN AUTHORIZATION
    # -----------------------------------------------------

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can approve return requests"
        )

    # -----------------------------------------------------
    # FIND RETURN REQUEST
    # -----------------------------------------------------

    return_request = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.id == return_id)
        .first()
    )

    if not return_request:
        raise HTTPException(
            status_code=404,
            detail="Return request not found"
        )

    # -----------------------------------------------------
    # ONLY PENDING RETURNS CAN BE APPROVED
    # -----------------------------------------------------

    if return_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending return requests can be approved"
        )

    # -----------------------------------------------------
    # FIND ORDER
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == return_request.order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found for this return request"
        )

    # -----------------------------------------------------
    # FIND CUSTOMER
    # -----------------------------------------------------

    customer = (
        db.query(User)
        .filter(User.id == return_request.user_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # -----------------------------------------------------
    # FIND PAYMENT
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found for this order"
        )

    # -----------------------------------------------------
    # CHECK STRIPE PAYMENT INTENT
    # -----------------------------------------------------

    if not payment.transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Stripe PaymentIntent ID is missing"
        )

    # -----------------------------------------------------
    # VALIDATE ORDER PRODUCTS
    # -----------------------------------------------------

    if not isinstance(order.products, list):
        raise HTTPException(
            status_code=400,
            detail="Order product information is invalid"
        )

    try:

        # =================================================
        # STEP 1: RESTORE INVENTORY
        # =================================================

        for item in order.products:

            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id:
                raise HTTPException(
                    status_code=400,
                    detail="Product ID missing in order item"
                )

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid quantity for product {product_id}"
                )

            if quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid quantity for product {product_id}"
                )

            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .first()
            )

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_id} not found"
                )

            product.stock_quantity = (
                (product.stock_quantity or 0) + quantity
            )

        # =================================================
        # STEP 2: CREATE STRIPE REFUND
        # =================================================

        refund = create_refund(
            payment_intent_id=payment.transaction_id,
            amount=payment.amount
        )

        # =================================================
        # STEP 3: UPDATE PAYMENT STATUS
        # =================================================

        payment.status = "refunded"

        # =================================================
        # STEP 4: UPDATE RETURN STATUS
        # =================================================

        return_request.status = "returned"

        # =================================================
        # STEP 4.1: UPDATE ORDER STATUS
        # =================================================

        order.order_status = "returned"

        # =================================================
        # STEP 5: RETURN APPROVED NOTIFICATION
        # =================================================

        approval_notification = Notification(
            user=customer.id,
            type="return_approved",
            message=(
                f"Your return request for Order #{order.id} "
                f"has been approved."
            ),
            read_status="unread"
        )

        db.add(approval_notification)

        # =================================================
        # STEP 6: REFUND COMPLETED NOTIFICATION
        # =================================================

        refund_notification = Notification(
            user=customer.id,
            type="refund_completed",
            message=(
                f"Your refund for Order #{order.id} "
                f"has been completed successfully."
            ),
            read_status="unread"
        )

        db.add(refund_notification)

        # =================================================
        # STEP 7: SAVE DATABASE CHANGES
        # =================================================

        db.commit()

        db.refresh(return_request)
        db.refresh(order)
        db.refresh(payment)

        # =================================================
        # STEP 8: PREPARE EMAIL DATA
        # =================================================

        customer_email = customer.email
        order_id = order.id
        order_products = order.products
        order_total = order.total
        refund_amount = payment.amount

        # =================================================
        # STEP 9: SEND RETURN APPROVED EMAIL
        # IN BACKGROUND
        # =================================================

        background_tasks.add_task(
            send_email,
            to_email=customer_email,
            order_id=order_id,
            status="return_approved",
            products=order_products,
            total_amount=order_total
        )

        # =================================================
        # STEP 10: SEND REFUND COMPLETED EMAIL
        # IN BACKGROUND
        # =================================================

        background_tasks.add_task(
            send_email,
            to_email=customer_email,
            order_id=order_id,
            status="refund_completed",
            products=order_products,
            total_amount=refund_amount
        )

        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return {
            "message": (
                "Return approved, inventory updated, "
                "payment refunded, order status updated, "
                "and notifications created successfully"
            ),
            "return_id": return_request.id,
            "status": return_request.status,
            "order_id": order.id,
            "order_status": order.order_status,
            "payment_id": payment.id,
            "payment_status": payment.status,
            "refund_id": refund.id,
            "notifications": [
                "return_approved",
                "refund_completed"
            ],
            "email_status": "queued"
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        print(
            f"Return approval failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process return, refund, "
                "inventory update, and notifications"
            )
        )


# =========================================================
# REJECT RETURN
# IN-APP + EMAIL NOTIFICATION
# =========================================================

@router.post("/{return_id}/reject")
def reject_return(
    return_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # -----------------------------------------------------
    # ADMIN AUTHORIZATION
    # -----------------------------------------------------

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can reject return requests"
        )

    # -----------------------------------------------------
    # FIND RETURN REQUEST
    # -----------------------------------------------------

    return_request = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.id == return_id)
        .first()
    )

    if not return_request:
        raise HTTPException(
            status_code=404,
            detail="Return request not found"
        )

    # -----------------------------------------------------
    # ONLY PENDING RETURNS CAN BE REJECTED
    # -----------------------------------------------------

    if return_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending return requests can be rejected"
        )

    # -----------------------------------------------------
    # FIND ORDER
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == return_request.order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found for this return request"
        )

    # -----------------------------------------------------
    # FIND CUSTOMER
    # -----------------------------------------------------

    customer = (
        db.query(User)
        .filter(User.id == return_request.user_id)
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    try:

        # =================================================
        # STEP 1: UPDATE RETURN STATUS
        # =================================================

        return_request.status = "rejected"

        # =================================================
        # STEP 2: CREATE IN-APP NOTIFICATION
        # =================================================

        rejection_notification = Notification(
            user=customer.id,
            type="return_rejected",
            message=(
                f"Your return request for Order #{order.id} "
                f"has been rejected."
            ),
            read_status="unread"
        )

        db.add(rejection_notification)

        # =================================================
        # STEP 3: SAVE DATABASE CHANGES
        # =================================================

        db.commit()

        db.refresh(return_request)

        # =================================================
        # STEP 4: SEND REJECTION EMAIL
        # IN BACKGROUND
        # =================================================

        background_tasks.add_task(
            send_email,
            to_email=customer.email,
            order_id=order.id,
            status="return_rejected",
            products=order.products,
            total_amount=order.total
        )

        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return {
            "message": (
                "Return request rejected and "
                "notification created successfully"
            ),
            "return_id": return_request.id,
            "status": return_request.status,
            "notification": "return_rejected",
            "email_status": "queued"
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        print(
            f"Return rejection failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to reject return request "
                "and create notification"
            )
        )