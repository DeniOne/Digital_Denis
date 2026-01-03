"""
Digital Den — Email Notifications Service
═══════════════════════════════════════════════════════════════════════════

Gmail SMTP integration for sending email notifications.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from dataclasses import dataclass

from core.logging import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EmailConfig:
    """Email configuration from environment."""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""  # App password for Gmail
    sender_name: str = "Digital Den"
    
    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Load configuration from environment variables."""
        return cls(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            sender_email=os.getenv("GMAIL_SMTP_USER", ""),
            sender_password=os.getenv("GMAIL_SMTP_PASSWORD", ""),
            sender_name=os.getenv("EMAIL_SENDER_NAME", "Digital Den"),
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.sender_email and self.sender_password)


# ═══════════════════════════════════════════════════════════════════════════
# Email Templates
# ═══════════════════════════════════════════════════════════════════════════

def get_reminder_email_html(title: str, time_str: str, description: str = None) -> str:
    """Generate HTML email for reminder notification."""
    
    desc_block = f"<p style='color:#666;margin-top:10px;'>{description}</p>" if description else ""
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,sans-serif;">
    <div style="max-width:600px;margin:20px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px;text-align:center;">
            <h1 style="color:white;margin:0;font-size:24px;">🔔 Напоминание</h1>
        </div>
        
        <!-- Content -->
        <div style="padding:30px;">
            <h2 style="color:#333;margin:0 0 10px 0;">{title}</h2>
            <p style="color:#667eea;font-size:18px;margin:0;">⏰ {time_str}</p>
            {desc_block}
        </div>
        
        <!-- Actions -->
        <div style="padding:0 30px 30px;text-align:center;">
            <a href="#" style="display:inline-block;background:#667eea;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;margin:5px;">✅ Выполнено</a>
            <a href="#" style="display:inline-block;background:#888;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;margin:5px;">⏰ Отложить</a>
        </div>
        
        <!-- Footer -->
        <div style="background:#f9f9f9;padding:20px;text-align:center;border-top:1px solid #eee;">
            <p style="color:#999;font-size:12px;margin:0;">
                Digital Den — Личный Когнитивный Помощник
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_reminder_email_text(title: str, time_str: str, description: str = None) -> str:
    """Generate plain text email for reminder notification."""
    
    text = f"""🔔 НАПОМИНАНИЕ

{title}
⏰ {time_str}
"""
    if description:
        text += f"\n{description}"
    
    text += """

---
Digital Den — Личный Когнитивный Помощник
"""
    return text


def get_schedule_summary_html(items: List[dict], date_str: str) -> str:
    """Generate HTML email for daily schedule summary."""
    
    items_html = ""
    for item in items:
        item_type = item.get("item_type", "reminder")
        emoji = {"event": "📌", "task": "📝", "reminder": "🔔"}.get(item_type, "•")
        time_str = item.get("time", "")
        title = item.get("title", "")
        
        items_html += f"""
        <tr>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <span style="font-size:18px;">{emoji}</span>
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <strong>{title}</strong><br>
                <span style="color:#888;font-size:14px;">⏰ {time_str}</span>
            </td>
        </tr>
        """
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,sans-serif;">
    <div style="max-width:600px;margin:20px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px;text-align:center;">
            <h1 style="color:white;margin:0;font-size:24px;">📅 Расписание на {date_str}</h1>
        </div>
        
        <!-- Content -->
        <div style="padding:20px;">
            <table style="width:100%;border-collapse:collapse;">
                {items_html}
            </table>
        </div>
        
        <!-- Footer -->
        <div style="background:#f9f9f9;padding:20px;text-align:center;border-top:1px solid #eee;">
            <p style="color:#999;font-size:12px;margin:0;">
                Digital Den — Личный Когнитивный Помощник
            </p>
        </div>
    </div>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════════════════
# Email Service
# ═══════════════════════════════════════════════════════════════════════════

class EmailService:
    """Service for sending emails via Gmail SMTP."""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env()
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email using Gmail SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (fallback)
            
        Returns:
            True if sent successfully, False otherwise
        """
        
        if not self.config.is_configured:
            logger.warning("Email not configured, skipping send")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.config.sender_name} <{self.config.sender_email}>"
            message["To"] = to_email
            
            # Add text part (fallback)
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)
            
            # Send via SMTP
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(
                    self.config.sender_email,
                    to_email,
                    message.as_string()
                )
            
            logger.info("email_sent", to=to_email, subject=subject[:50])
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("email_auth_error", error=str(e))
            return False
        except smtplib.SMTPException as e:
            logger.error("smtp_error", error=str(e))
            return False
        except Exception as e:
            logger.error("email_send_error", error=str(e))
            return False
    
    async def send_reminder(
        self,
        to_email: str,
        title: str,
        remind_at: str,
        description: Optional[str] = None,
    ) -> bool:
        """Send a reminder notification email."""
        
        html = get_reminder_email_html(title, remind_at, description)
        text = get_reminder_email_text(title, remind_at, description)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"🔔 Напоминание: {title}",
            html_content=html,
            text_content=text,
        )
    
    async def send_schedule_summary(
        self,
        to_email: str,
        items: List[dict],
        date_str: str,
    ) -> bool:
        """Send daily schedule summary email."""
        
        if not items:
            return False
        
        html = get_schedule_summary_html(items, date_str)
        
        return await self.send_email(
            to_email=to_email,
            subject=f"📅 Расписание на {date_str}",
            html_content=html,
        )


# Global instance
email_service = EmailService()
