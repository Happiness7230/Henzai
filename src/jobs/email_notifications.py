import logging
from email.mime.text import MIMEText
import smtplib

logger = logging.getLogger(__name__)

# ----------------------------
# Email Configuration
# ----------------------------
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"   # For Gmail, generate an App Password


def _send_email(to_email: str, subject: str, body: str):
    """
    Internal reusable function to send emails via SMTP.
    """
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = SMTP_USERNAME
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())

        logger.info(f"Email sent to {to_email} — {subject}")

    except Exception as e:
        logger.error(f"Email send failure ({to_email}): {e}")
        raise
def send_job_alert_email(alert: dict, jobs: list):
    """
    Sends job alert email notification to user based on matched job results.
    """
    user_email = alert["email"]
    subject = f"Job Alert — New jobs found for '{alert['keywords']}'"

    job_lines = []
    for job in jobs:
        job_lines.append(
            f"{job['title']} — {job['company']} ({job['location']})\n{job['url']}"
        )

    body = (
        f"Hello,\n\n"
        f"We found new job matches for your alert:\n\n"
        f"Keywords: {alert['keywords']}\n"
        f"Location: {alert['location']}\n\n"
        f"Top results:\n\n"
        + "\n\n".join(job_lines)
        + "\n\nRegards,\nNexus Search Engine"
    )

    _send_email(user_email, subject, body)
def send_price_alert_email(alert: dict, product: dict):
    """
    Sends price alert notification when tracked product price drops.
    """
    user_email = alert["email"]
    subject = f"Price Alert — {product['title']} is now {product['price']}"

    body = (
        f"Hello,\n\n"
        f"The price of a product you're tracking has dropped!\n\n"
        f"Product: {product['title']}\n"
        f"Current Price: {product['price']}\n"
        f"Previous Price: {product['old_price']}\n"
        f"Link: {product['url']}\n\n"
        f"Regards,\nNexus Search Engine"
    )

    _send_email(user_email, subject, body)
def send_general_notification(email: str, subject: str, message: str):
    """
    General-purpose notification email for newsletters, system updates, etc.
    """
    body = f"{message}\n\nRegards,\nNexus Search Engine"
    _send_email(email, subject, body)
