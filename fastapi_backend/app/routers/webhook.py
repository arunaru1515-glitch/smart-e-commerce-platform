import os
import stripe

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.payment import Payment


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

        # =================================================
        # Stripe Payment Intent ID
        # =================================================

        stripe_payment_intent_id = payment_intent["id"]

        # =================================================
        # Find Payment Using Stripe Transaction ID
        # =================================================

        payment = db.query(Payment).filter(
            Payment.transaction_id == stripe_payment_intent_id
        ).first()

        # =================================================
        # Payment Record Not Found
        # =================================================

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment record not found"
            )

        # =================================================
        # Get Order ID Directly From Payment Record
        # =================================================

        order_id = payment.order_id

        # =================================================
        # Find Order
        # =================================================

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
        # Save Changes
        # =================================================

        db.commit()

        # =================================================
        # Refresh Database Objects
        # =================================================

        db.refresh(payment)
        db.refresh(order)

        # =================================================
        # Success Response
        # =================================================

        return {
            "message": "Payment successful",
            "order_id": order.id,
            "payment_id": payment.id,
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

        payment = db.query(Payment).filter(
            Payment.transaction_id == stripe_payment_intent_id
        ).first()

        if payment:
            payment.status = "failed"

            order = db.query(Order).filter(
                Order.id == payment.order_id
            ).first()

            if order:
                order.payment_status = "failed"

            db.commit()

        return {
            "message": "Payment failed",
            "payment_id": stripe_payment_intent_id
        }

    # =====================================================
    # Other Stripe Events
    # =====================================================

    return {
        "message": "Webhook received",
        "event_type": event["type"]
    }