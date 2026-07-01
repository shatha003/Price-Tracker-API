import os
import sys

from dotenv import load_dotenv

from email_notifier import send_price_alert

load_dotenv()

smtp_host = os.getenv("SMTP_HOST", "")
if not smtp_host:
    print("ERROR: SMTP not configured. Copy .env.example to .env and fill in your SMTP credentials.")
    print("For Gmail, you need an App Password (enable 2FA first): https://myaccount.google.com/apppasswords")
    exit(1)

to_email = sys.argv[1] if len(sys.argv) > 1 else "shathakhlifat@gmail.com"

success = send_price_alert(
    to_email=to_email,
    product_url="https://a.co/d/0dXiFF6S",
    price=99.99,
    target_price=188.0,
)

if success:
    print(f"Email sent successfully to {to_email}! Check your inbox.")
else:
    print(f"Failed to send email. Check your SMTP credentials in .env")
