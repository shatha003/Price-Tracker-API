import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_price_alert(to_email: str, product_url: str, price: float, target_price: float) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)

    if not smtp_host or not smtp_user or not smtp_pass:
        return False

    subject = f"Price Drop Alert: ${price:.2f} (target: ${target_price:.2f})"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    text = f"The price for {product_url} has dropped to ${price:.2f} (your target: ${target_price:.2f})."
    html = f"""<html><body style="font-family:Arial;padding:20px">
<h2>Price Drop Alert</h2>
<p>The price for <a href="{product_url}">{product_url}</a> has dropped to <strong>${price:.2f}</strong>.</p>
<p>Your target price was: <strong>${target_price:.2f}</strong></p>
<hr><p style="color:#888">Sent by Price Tracker API</p>
</body></html>"""

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())
        print(f"Email sent to {to_email} for {product_url}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
