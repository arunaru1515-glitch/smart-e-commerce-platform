import os
import stripe

from dotenv import load_dotenv

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.order import Order
from app.models.payment import Payment
from app.models.notification import Notification
from app.models.user import User

from app.services.email_service import send_email


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# Stripe Webhook Router
# =========================================================

router = APIRouter(
    prefix="/webhook",
    tags=["Stripe Webhook"]
)


# =========================================================
# Stripe Configuration
# =========================================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =========================================================
# Stripe Webhook Endpoint
# =========================================================

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    # =====================================================
    # Read Raw Stripe Webhook Payload
    # =====================================================

    payload = await request.body()

    signature = request.headers.get("stripe-signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret is not configured"
        )

    # =====================================================
    # Verify Stripe Webhook Signature
    # =====================================================

    try:

        event = stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload"
        )

    except stripe.error.SignatureVerificationError:

        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature"
        )

    # =====================================================
    # Payment Intent Succeeded
    # =====================================================

    if event["type"] == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        stripe_payment_intent_id = payment_intent["id"]

        # =================================================
        # Find Payment
        # =================================================

        payment = db.query(Payment).filter(
            Payment.transaction_id == stripe_payment_intent_id
        ).first()

        if not payment:

            raise HTTPException(
                status_code=404,
                detail="Payment record not found"
            )

        # =================================================
        # Get Order
        # =================================================

        order_id = payment.order_id

        order = db.query(Order).filter(
            Order.id == order_id
        ).first()

        if not order:

            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        # =================================================
        # Update Payment Status
        # =================================================

        payment.status = "paid"

        # =================================================
        # Update Order Status
        # =================================================

        order.payment_status = "paid"
        order.order_status = "paid"

        # =================================================
        # Create Payment Success Notification
        # =================================================

        notification = Notification(
            user=order.user,
            type="payment",
            message=(
                f"Payment successful for Order #{order.id}. "
                f"Amount: ₹{payment.amount}"
            ),
            read_status="unread"
        )

        db.add(notification)

        # =================================================
        # Save Changes
        # =================================================

        db.commit()

        # =================================================
        # Refresh Database Objects
        # =================================================

        db.refresh(payment)
        db.refresh(order)
        db.refresh(notification)

        # =================================================
        # GET USER
        # =================================================

        user = db.query(User).filter(
            User.id == order.user
        ).first()

        # =================================================
        # SEND PAYMENT SUCCESS EMAIL
        # =================================================

        if user and user.email:

            send_email(
                to_email=user.email,
                subject="Payment Successful - Smart E-Commerce Platform",
                message=(
                    f"Hello,\n\n"
                    f"Your payment was successful.\n\n"
                    f"Order ID: #{order.id}\n"
                    f"Amount: ₹{payment.amount}\n"
                    f"Payment Status: Paid\n\n"
                    f"Thank you for shopping with us."
                )
            )

        # =================================================
        # Success Response
        # =================================================

        return {
            "message": "Payment successful",
            "order_id": order.id,
            "payment_id": payment.id,
            "notification_id": notification.id,
            "payment_status": payment.status,
            "order_payment_status": order.payment_status,
            "order_status": order.order_status
        }

    # =====================================================
    # Payment Intent Failed
    # =====================================================

    if event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        stripe_payment_intent_id = payment_intent["id"]

        # =================================================
        # Find Payment
        # =================================================

        payment = db.query(Payment).filter(
            Payment.transaction_id == stripe_payment_intent_id
        ).first()

        if payment:

            # =============================================
            # Update Payment Status
            # =============================================

            payment.status = "failed"

            # =============================================
            # Get Order
            # =============================================

            order = db.query(Order).filter(
                Order.id == payment.order_id
            ).first()

            notification = None

            if order:

                # =========================================
                # Update Order Payment Status
                # =========================================

                order.payment_status = "failed"

                # =========================================
                # Create Payment Failed Notification
                # =========================================

                notification = Notification(
                    user=order.user,
                    type="payment_failed",
                    message=(
                        f"Payment failed for Order #{order.id}. "
                        f"Please try again."
                    ),
                    read_status="unread"
                )

                db.add(notification)

            # =============================================
            # Save Changes
            # =============================================

            db.commit()

            # =============================================
            # Refresh Objects
            # =============================================

            db.refresh(payment)

            if order:
                db.refresh(order)

            if notification:
                db.refresh(notification)

            # =============================================
            # Response
            # =============================================

            return {
                "message": "Payment failed",
                "payment_id": payment.id,
                "order_id": (
                    order.id
                    if order
                    else None
                ),
                "notification_id": (
                    notification.id
                    if notification
                    else None
                ),
                "payment_status": payment.status,
                "order_payment_status": (
                    order.payment_status
                    if order
                    else None
                )
            }

        # =================================================
        # Payment Record Not Found
        # =================================================

        return {
            "message": "Payment record not found",
            "payment_id": stripe_payment_intent_id
        }

    # =====================================================
    # Other Stripe Events
    # =====================================================

    return {
        "message": "Webhook received",
        "event_type": event["type"]
    }