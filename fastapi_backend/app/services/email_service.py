import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

# Load .env
load_dotenv()


def send_email(
    to_email: str,
    order_id: int,
    status: str
):
    """
    Send order status update email to customer.
    """

    # SMTP configuration
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

    # Validate configuration
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

    # Email subject
    subject = (
        f"Order #{order_id} Status Update"
    )

    # Email body
    message = f"""
Hello,

Your Order #{order_id} status has been updated.

Current Status: {status.upper()}

Thank you for shopping with Smart E-Commerce Platform.

Regards,
Smart E-Commerce Platform
"""

    # Create email
    email = EmailMessage()

    email["From"] = sender_email
    email["To"] = to_email
    email["Subject"] = subject

    email.set_content(message)

    try:

        # Gmail SMTP connection
        if smtp_port == 465:

            # SSL connection
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port
            ) as smtp:

                smtp.login(
                    sender_email,
                    sender_password
                )

                smtp.send_message(email)

        else:

            # STARTTLS connection
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

                smtp.send_message(email)

        print(
            f"Email sent successfully to {to_email}"
        )

        return True

    except Exception as e:

        print(
            f"Email sending failed: {str(e)}"
        )

        raise


# Backward-compatible function
def send_order_status_email(
    to_email: str,
    order_id: int,
    status: str
):
    """
    Send order status email.
    """

    return send_email(
        to_email=to_email,
        order_id=order_id,
        status=status
    )