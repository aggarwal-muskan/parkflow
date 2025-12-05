# backend/emailer.py
import smtplib
from email.mime.text import MIMEText

# TODO: put your actual email + app password here
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "21f3002431@ds.study.iitm.ac.in"      # your Gmail address
SMTP_PASS = "muskan0207"   # Gmail App Password (NOT your normal password)
EMAIL_FROM = SMTP_USER


def send_email(to: str, subject: str, html: str):
    """
    Send a simple HTML email.
    'to' should be a real email address.
    """
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to

    try:
      with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
          server.starttls()
          server.login(SMTP_USER, SMTP_PASS)
          server.send_message(msg)

      print(f"[EMAIL] Sent '{subject}' to {to}")

    except Exception as e:
      print(f"[EMAIL ERROR] Could not send email to {to}: {e}")