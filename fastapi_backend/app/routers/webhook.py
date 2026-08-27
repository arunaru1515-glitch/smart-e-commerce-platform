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
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product

from app.services.email_service import send_order_status_email


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# STRIPE WEBHOOK ROUTER
# =========================================================

router = APIRouter(
    prefix="/webhook",
    tags=["Stripe Webhook"]
)


# =========================================================
# STRIPE CONFIGURATION
# =========================================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =========================================================
# STRIPE WEBHOOK ENDPOINT
# POST /webhook/stripe
# =========================================================

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. READ RAW STRIPE PAYLOAD
    # =====================================================

    payload = await request.body()

    signature = request.headers.get("stripe-signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="Stripe webhook secret is not configured"
        )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Stripe signature is missing"
        )


    # =====================================================
    # 2. VERIFY STRIPE WEBHOOK
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
    # 3. PAYMENT INTENT SUCCEEDED
    # =====================================================

    if event["type"] == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        stripe_payment_intent_id = payment_intent["id"]


        # =================================================
        # FIND PAYMENT
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
        # FIND ORDER
        # =================================================

        order = db.query(Order).filter(
            Order.id == payment.order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )


        # =================================================
        # GET USER
        # =================================================

        user = db.query(User).filter(
            User.id == order.user
        ).first()


        # =================================================
        # PREVENT DUPLICATE PROCESSING
        # =================================================

        if payment.status == "paid":

            return {
                "message": "Payment already processed",
                "order_id": order.id,
                "payment_id": payment.id,
                "payment_status": payment.status,
                "order_payment_status": order.payment_status,
                "order_status": order.order_status
            }


        # =================================================
        # UPDATE PAYMENT STATUS
        # =================================================

        payment.status = "paid"


        # =================================================
        # UPDATE ORDER STATUS
        # =================================================

        order.payment_status = "paid"
        order.order_status = "paid"


        # =================================================
        # FIND USER CART
        # =================================================

        cart = db.query(Cart).filter(
            Cart.user_id == order.user
        ).first()


        # =================================================
        # GET CART ITEMS
        # =================================================

        cart_items = []

        if cart:

            cart_items = db.query(CartItem).filter(
                CartItem.cart_id == cart.id
            ).all()


        # =================================================
        # REDUCE PRODUCT STOCK
        # =================================================

        for cart_item in cart_items:

            product = db.query(Product).filter(
                Product.id == cart_item.product_id
            ).first()

            if product:

                product.stock_quantity = max(
                    0,
                    product.stock_quantity - cart_item.quantity
                )

                product.is_available = (
                    product.stock_quantity > 0
                )


        # =================================================
        # CLEAR CART AFTER SUCCESSFUL PAYMENT
        # =================================================

        for cart_item in cart_items:

            db.delete(cart_item)


        # =================================================
        # CREATE SUCCESS NOTIFICATION
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
        # SAVE DATABASE CHANGES
        # =================================================

        try:

            db.commit()

            db.refresh(payment)
            db.refresh(order)
            db.refresh(notification)

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )


        # =================================================
        # SEND SUCCESS EMAIL
        # =================================================

        email_sent = False

        if user and user.email:

            try:

                send_order_status_email(
                    to_email=user.email,
                    order_id=order.id,
                    status="paid"
                )

                email_sent = True

            except Exception as e:

                print(
                    f"Email sending failed: {str(e)}"
                )


        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return {
            "message": "Payment successful",
            "order_id": order.id,
            "payment_id": payment.id,
            "notification_id": notification.id,
            "payment_status": payment.status,
            "order_payment_status": order.payment_status,
            "order_status": order.order_status,
            "stock_updated": True,
            "cart_cleared": True,
            "email_sent": email_sent
        }


    # =====================================================
    # 4. PAYMENT INTENT FAILED
    # =====================================================

    if event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        stripe_payment_intent_id = payment_intent["id"]


        # =================================================
        # FIND PAYMENT
        # =================================================

        payment = db.query(Payment).filter(
            Payment.transaction_id == stripe_payment_intent_id
        ).first()

        if not payment:

            return {
                "message": "Payment record not found",
                "payment_id": stripe_payment_intent_id
            }


        # =================================================
        # FIND ORDER
        # =================================================

        order = db.query(Order).filter(
            Order.id == payment.order_id
        ).first()


        # =================================================
        # UPDATE PAYMENT
        # =================================================

        payment.status = "failed"

        notification = None
        user = None


        # =================================================
        # UPDATE ORDER
        # =================================================

        if order:

            order.payment_status = "failed"

            user = db.query(User).filter(
                User.id == order.user
            ).first()


            # =============================================
            # CREATE FAILURE NOTIFICATION
            # =============================================

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


        # =================================================
        # SAVE DATABASE CHANGES
        # =================================================

        try:

            db.commit()

            db.refresh(payment)

            if order:
                db.refresh(order)

            if notification:
                db.refresh(notification)

        except Exception as e:

            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )


        # =================================================
        # SEND FAILURE EMAIL
        # =================================================

        email_sent = False

        if user and user.email and order:

            try:

                send_order_status_email(
                    to_email=user.email,
                    order_id=order.id,
                    status="failed"
                )

                email_sent = True

            except Exception as e:

                print(
                    f"Email sending failed: {str(e)}"
                )


        # =================================================
        # FAILURE RESPONSE
        # =================================================

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
            ),
            "email_sent": email_sent
        }


    # =====================================================
    # 5. OTHER STRIPE EVENTS
    # =====================================================

    return {
        "message": "Webhook received",
        "event_type": event["type"]
    }