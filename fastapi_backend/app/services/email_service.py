import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def send_order_status_email(
    to_email: str,
    order_id: int,
    status: str
):
    """
    Send order status update email to customer.
    """

    sender_email = os.getenv("EMAIL_USERNAME")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        raise Exception(
            "Email configuration is missing in .env"
        )

    subject = f"Order #{order_id} Status Update"

    message = f"""
Hello,

Your Order #{order_id} status has been updated.

Current Status: {status.upper()}

Thank you for shopping with Smart E-Commerce Platform.

Regards,
Smart E-Commerce Platform
"""

    email = EmailMessage()

    email["From"] = sender_email
    email["To"] = to_email
    email["Subject"] = subject

    email.set_content(message)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender_email,
            sender_password
        )

        smtp.send_message(email)

    return True