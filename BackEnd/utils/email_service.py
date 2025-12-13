import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Default to Gmail if not set
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "amarzuher635@gmail.com")     # User must set this
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "amarzuher635") # User must set this (App Password)

def send_email_otp(to_email: str, otp_code: str):
    """
    Send OTP via Email using SMTP.
    Returns True if successful, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️ SMTP credentials not set. Skipping email.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Verification Code - TradeAI"
        
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; text-align: center; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
              <h2 style="color: #4CAF50;">TradeAI Registration</h2>
              <p>Please use the following code to verify your email address:</p>
              <div style="background-color: #f5f5f5; padding: 15px; font-size: 24px; letter-spacing: 5px; font-weight: bold; border-radius: 5px; margin: 20px 0;">
                {otp_code}
              </div>
              <p style="font-size: 12px; color: #999;">This code will expire in 10 minutes.</p>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"📧 Email sent successfully to {to_email}", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}", flush=True)
        return False
