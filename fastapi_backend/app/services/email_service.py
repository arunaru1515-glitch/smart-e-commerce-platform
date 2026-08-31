import os
import smtplib

from email.message import EmailMessage
from decimal import Decimal

from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(
    to_email: str,
    order_id: int,
    status: str,
    products=None,
    total_amount=None
):
    """
    Send order status email to customer.

    Supported statuses:
        paid
        shipped
        delivered
        cancelled

    Product format:
    [
        {
            "name": "Headphones",
            "quantity": 1,
            "unit_price": 3500
        }
    ]
    """

    # =====================================================
    # SMTP CONFIGURATION
    # =====================================================

    smtp_host = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    sender_email = os.getenv(
        "SMTP_USERNAME"
    )

    sender_password = os.getenv(
        "SMTP_PASSWORD"
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    if not sender_email:
        raise Exception(
            "SMTP_USERNAME is missing in .env"
        )

    if not sender_password:
        raise Exception(
            "SMTP_PASSWORD is missing in .env"
        )

    if not to_email:
        raise Exception(
            "Customer email is missing"
        )


    # =====================================================
    # DEFAULT VALUES
    # =====================================================

    if products is None:
        products = []

    if total_amount is None:
        total_amount = Decimal("0")


    # =====================================================
    # NORMALIZE STATUS
    # =====================================================

    status = str(status).lower().strip()


    # =====================================================
    # STATUS-SPECIFIC EMAIL CONTENT
    # =====================================================

    if status == "paid":

        subject = (
            f"Order #{order_id} Payment Confirmation"
        )

        greeting_message = (
            f"Your payment for Order #{order_id} "
            f"has been successfully received."
        )

        status_title = "PAYMENT CONFIRMED"

        status_label = "Payment Status"

        status_value = "PAID"

        final_message = (
            "Your payment has been securely processed "
            "and your order has been confirmed."
        )


    elif status == "shipped":

        subject = (
            f"Your Order #{order_id} Has Been Shipped"
        )

        greeting_message = (
            f"Good news! Your Order #{order_id} "
            f"has been shipped and is on its way."
        )

        status_title = "ORDER SHIPPED"

        status_label = "Order Status"

        status_value = "SHIPPED"

        final_message = (
            "Your order is on its way. "
            "You will receive another notification "
            "when your order is delivered."
        )


    elif status == "delivered":

        subject = (
            f"Your Order #{order_id} Has Been Delivered"
        )

        greeting_message = (
            f"Your Order #{order_id} "
            f"has been successfully delivered."
        )

        status_title = "ORDER DELIVERED"

        status_label = "Order Status"

        status_value = "DELIVERED"

        final_message = (
            "We hope you enjoy your purchase. "
            "Thank you for shopping with us."
        )


    elif status == "cancelled":

        subject = (
            f"Order #{order_id} Has Been Cancelled"
        )

        greeting_message = (
            f"Your Order #{order_id} "
            f"has been cancelled."
        )

        status_title = "ORDER CANCELLED"

        status_label = "Order Status"

        status_value = "CANCELLED"

        final_message = (
            "If you believe this cancellation was made "
            "in error, please contact our support team."
        )


    else:

        subject = (
            f"Order #{order_id} Status Update"
        )

        greeting_message = (
            f"The status of your Order #{order_id} "
            f"has been updated."
        )

        status_title = "ORDER STATUS UPDATE"

        status_label = "Order Status"

        status_value = status.upper()

        final_message = (
            "Thank you for shopping with "
            "Smart E-Commerce Platform."
        )


    # =====================================================
    # FORMAT PRODUCT DETAILS
    # =====================================================

    product_lines = []


    for index, product in enumerate(
        products,
        start=1
    ):

        if not isinstance(product, dict):
            continue


        # -------------------------------------------------
        # PRODUCT NAME
        # -------------------------------------------------

        product_name = (
            product.get("name")
            or product.get("product_name")
            or product.get("productName")
            or product.get("title")
            or "Product"
        )


        # -------------------------------------------------
        # QUANTITY
        # -------------------------------------------------

        quantity = (
            product.get("quantity")
            or product.get("qty")
            or 1
        )


        # -------------------------------------------------
        # UNIT PRICE
        # -------------------------------------------------

        unit_price = (
            product.get("unit_price")
            if product.get("unit_price") is not None
            else product.get("price")
        )


        if unit_price is None:
            unit_price = 0


        # -------------------------------------------------
        # CALCULATE ITEM TOTAL
        # -------------------------------------------------

        try:

            unit_price_decimal = Decimal(
                str(unit_price)
            )

            quantity_decimal = Decimal(
                str(quantity)
            )

            item_total = (
                unit_price_decimal *
                quantity_decimal
            )

        except Exception:

            unit_price_decimal = Decimal("0")

            item_total = Decimal("0")


        # -------------------------------------------------
        # PRODUCT DETAILS
        # -------------------------------------------------

        product_lines.append(
            f"{index}. {product_name}\n"
            f"   Quantity   : {quantity}\n"
            f"   Unit Price : ₹{unit_price_decimal:,.2f}\n"
            f"   Item Total : ₹{item_total:,.2f}"
        )


    if product_lines:

        products_text = "\n\n".join(
            product_lines
        )

    else:

        products_text = (
            "Product details are not available."
        )


    # =====================================================
    # FORMAT TOTAL
    # =====================================================

    try:

        total_decimal = Decimal(
            str(total_amount)
        )

        total_text = (
            f"₹{total_decimal:,.2f}"
        )

    except Exception:

        total_text = (
            f"₹{total_amount}"
        )


    # =====================================================
    # EMAIL BODY
    # =====================================================

    message = f"""
Hello,

Thank you for shopping with Smart E-Commerce Platform.

{greeting_message}

==================================================
                 {status_title}
==================================================

Order ID        : #{order_id}
{status_label:<16}: {status_value}

--------------------------------------------------
                 PRODUCT DETAILS
--------------------------------------------------

{products_text}

--------------------------------------------------
                 ORDER SUMMARY
--------------------------------------------------

Total Amount    : {total_text}

==================================================

{final_message}

Thank you for choosing Smart E-Commerce Platform.

Regards,
Smart E-Commerce Platform
"""


    # =====================================================
    # CREATE EMAIL
    # =====================================================

    email = EmailMessage()

    email["From"] = sender_email

    email["To"] = to_email

    email["Subject"] = subject

    email.set_content(
        message
    )


    # =====================================================
    # SEND EMAIL
    # =====================================================

    try:

        # -------------------------------------------------
        # SSL
        # -------------------------------------------------

        if smtp_port == 465:

            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port
            ) as smtp:

                smtp.login(
                    sender_email,
                    sender_password
                )

                smtp.send_message(
                    email
                )


        # -------------------------------------------------
        # STARTTLS
        # -------------------------------------------------

        else:

            with smtplib.SMTP(
                smtp_host,
                smtp_port
            ) as smtp:

                smtp.ehlo()

                smtp.starttls()

                smtp.ehlo()

                smtp.login(
                    sender_email,
                    sender_password
                )

                smtp.send_message(
                    email
                )


        print(
            f"Email sent successfully to {to_email}"
        )

        return True


    except Exception as e:

        print(
            f"Email sending failed: {str(e)}"
        )

        raise


# =========================================================
# BACKWARD-COMPATIBLE FUNCTION
# =========================================================

def send_order_status_email(
    to_email: str,
    order_id: int,
    status: str,
    products=None,
    total_amount=None
):
    """
    Send order status email.
    """

    return send_email(
        to_email=to_email,
        order_id=order_id,
        status=status,
        products=products,
        total_amount=total_amount
    )