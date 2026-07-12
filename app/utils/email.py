import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def _get_sender_domain() -> str:
    from_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER or "servease.com"
    if "@" in from_email:
        return from_email.split("@")[-1]
    return "servease.com"

def send_contact_email(first_name: str, last_name: str, email: str, message: str) -> None:
    subject = f"New Contact Inquiry: {first_name} {last_name}"
    body = f"""You have received a new contact inquiry.

Name: {first_name} {last_name}
Sender Email: {email}

Message:
--------------------------------------------------
{message}
--------------------------------------------------
"""

    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD and settings.EMAILS_TO_EMAIL):
        logger.warning("SMTP settings not fully configured. Printing contact message to console instead.")
        print("\n=== [DEBUG] CONTACT FORM EMAIL ===")
        print(f"To: {settings.EMAILS_TO_EMAIL or 'Not Configured'}")
        print(f"From (Sender field): {email}")
        print(f"SMTP From: {settings.EMAILS_FROM_EMAIL or 'Not Configured'}")
        print(f"Subject: {subject}")
        print(f"Content:\n{body}")
        print("===================================\n")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
        msg['To'] = settings.EMAILS_TO_EMAIL
        msg['Reply-To'] = email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=_get_sender_domain())
        msg['MIME-Version'] = '1.0'
        msg['Auto-Submitted'] = 'auto-generated'

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if settings.SMTP_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
            if settings.SMTP_TLS:
                server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.quit()
        logger.info(f"Successfully sent contact inquiry email from {email} to {settings.EMAILS_TO_EMAIL}")
    except Exception as e:
        logger.error(f"Failed to send contact email via SMTP: {e}")
        # Print to console as a fallback in case SMTP fails during live execution
        print("\n=== [FALLBACK] CONTACT FORM EMAIL ===")
        print(f"SMTP Error: {e}")
        print(f"To: {settings.EMAILS_TO_EMAIL}")
        print(f"Sender Email: {email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{body}")
        print("======================================\n")

def send_otp_email(to_email: str, otp_code: str) -> None:
    subject = f"Your Serviz Verification Code: {otp_code}"
    
    # Plain text version for fallback
    body_text = f"""Your Serviz verification code is: {otp_code}

This code is valid for 10 minutes. If you did not request this code, you can safely ignore this email.

Regards,
Serviz Team
"""

    # Beautiful HTML version with clean, high-reputation, professional light/neutral aesthetics
    body_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Serviz Verification Code</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 40px 10px; color: #333333; -webkit-font-smoothing: antialiased;">
  <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
    <!-- Header -->
    <tr>
      <td style="background-color: #ffffff; padding: 32px 24px; text-align: center; border-bottom: 1px solid #f1f3f5;">
        <div style="font-size: 24px; font-weight: 800; color: #1a1a1a; letter-spacing: 1px; text-transform: uppercase;">
          SERVIZ
        </div>
      </td>
    </tr>
    
    <!-- Body Content -->
    <tr>
      <td style="padding: 40px 32px; text-align: center;">
        <h2 style="font-size: 20px; font-weight: 600; color: #212529; margin-top: 0; margin-bottom: 16px;">
          Verification Code
        </h2>
        
        <p style="font-size: 15px; line-height: 1.5; color: #495057; margin-bottom: 32px;">
          Please use the 6-digit verification code below to authorize your session:
        </p>
        
        <!-- OTP Display Box -->
        <table align="center" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
          <tr>
            <td style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 16px 32px; text-align: center;">
              <span style="font-family: 'Courier New', Courier, monospace, sans-serif; font-size: 32px; font-weight: 700; color: #000000; letter-spacing: 6px;">
                {otp_code}
              </span>
            </td>
          </tr>
        </table>
        
        <p style="font-size: 13px; color: #868e96; margin-top: 16px; margin-bottom: 32px;">
          This verification code is valid for <strong>10 minutes</strong>.
        </p>
        
        <div style="background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; padding: 16px; text-align: left;">
          <p style="font-size: 13px; line-height: 1.5; color: #6c757d; margin: 0;">
            If you did not request this verification code, you can safely ignore this email.
          </p>
        </div>
      </td>
    </tr>
    
    <!-- Footer -->
    <tr>
      <td style="background-color: #f8f9fa; padding: 24px; text-align: center; border-top: 1px solid #dee2e6; font-size: 12px; color: #868e96; line-height: 1.5;">
        This email was sent automatically from a monitored system. Please do not reply directly.<br>
        &copy; 2026 Serviz Inc. All Rights Reserved.
      </td>
    </tr>
  </table>
</body>
</html>
"""

    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
        logger.warning("SMTP settings not fully configured. Printing OTP to console instead.")
        print("\n=== [DEBUG] ADMIN OTP EMAIL ===")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"OTP: {otp_code}")
        print("===============================\n")
        return

    try:
        # Use multipart/alternative to support both plain text and HTML fallbacks
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain=_get_sender_domain())
        msg['MIME-Version'] = '1.0'
        msg['Auto-Submitted'] = 'auto-generated'
        msg['X-Auto-Response-Suppress'] = 'All'

        # Attach text first, then html
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        if settings.SMTP_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
            if settings.SMTP_TLS:
                server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg['From'], [to_email], msg.as_string())
        server.quit()
        logger.info(f"Successfully sent Admin OTP HTML email to {to_email}")
        
        # Print to console for development visibility
        print(f"\n>>> [DEV] OTP CODE SENT TO {to_email}: {otp_code} <<<\n")
        
        # Write to local file for absolute reliability during testing
        try:
            with open("otp_debug.txt", "w") as f:
                f.write(otp_code)
        except Exception as write_err:
            logger.error(f"Failed to write otp_debug.txt: {write_err}")
            
    except Exception as e:
        logger.error(f"Failed to send Admin OTP email via SMTP: {e}")
        # Print to console as fallback
        print("\n=== [FALLBACK] ADMIN OTP EMAIL ===")
        print(f"SMTP Error: {e}")
        print(f"To: {to_email}")
        print(f"OTP: {otp_code}")
        print("==================================\n")
        
        # Write to local file for absolute reliability during testing
        try:
            with open("otp_debug.txt", "w") as f:
                f.write(otp_code)
        except Exception as write_err:
            logger.error(f"Failed to write otp_debug.txt: {write_err}")

