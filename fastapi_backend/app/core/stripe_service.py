import os
from decimal import Decimal

import stripe
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# STRIPE CONFIGURATION
# =========================================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# =========================================================
# CREATE PAYMENT INTENT
# =========================================================

def create_payment_intent(
    amount: Decimal,
    order_id: int
):
    """
    Create a Stripe PaymentIntent for an order.

    Stripe expects the amount in the smallest
    currency unit. For INR, this means paise.
    """

    amount_in_paise = int(
        Decimal(str(amount)) * 100
    )

    payment_intent = stripe.PaymentIntent.create(
        amount=amount_in_paise,
        currency="inr",
        metadata={
            "order_id": str(order_id)
        }
    )

    return payment_intent