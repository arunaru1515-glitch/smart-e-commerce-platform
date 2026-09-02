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

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    raise RuntimeError(
        "STRIPE_SECRET_KEY is missing in .env"
    )

stripe.api_key = STRIPE_SECRET_KEY


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

    amount_decimal = Decimal(str(amount))

    if amount_decimal <= Decimal("0.00"):
        raise ValueError(
            "Payment amount must be greater than zero"
        )

    amount_in_paise = int(
        amount_decimal * 100
    )

    payment_intent = stripe.PaymentIntent.create(
        amount=amount_in_paise,
        currency="inr",
        metadata={
            "order_id": str(order_id)
        }
    )

    return payment_intent


# =========================================================
# CREATE STRIPE REFUND
# =========================================================

def create_refund(
    payment_intent_id: str,
    amount: Decimal
):
    """
    Create a Stripe refund for a PaymentIntent.

    Stripe expects the refund amount in the
    smallest currency unit. For INR, this means paise.
    """

    if not payment_intent_id:
        raise ValueError(
            "Stripe PaymentIntent ID is missing"
        )

    amount_decimal = Decimal(str(amount))

    if amount_decimal <= Decimal("0.00"):
        raise ValueError(
            "Refund amount must be greater than zero"
        )

    amount_in_paise = int(
        amount_decimal * 100
    )

    refund = stripe.Refund.create(
        payment_intent=payment_intent_id,
        amount=amount_in_paise
    )

    return refund