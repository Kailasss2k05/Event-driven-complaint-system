import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import logging
from typing import Dict, Optional

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        # Gmail app passwords are shown with spaces but used without them
        raw_password = os.getenv("SENDER_PASSWORD", "")
        self.sender_password = raw_password.replace(" ", "")
        self.sender_name = os.getenv("SENDER_NAME", "Municipal Complaint System")
        
        # Email templates
        self.templates = {
            "complaint_submitted": {
                "subject": "Complaint Submitted Successfully - #{complaint_id}",
                "body": """
Dear {user_name},

Your complaint has been successfully submitted to the Municipal Complaint System.

--------------------------------------------------
Complaint ID   : {complaint_id}
Description    : {description}
--------------------------------------------------

Our system will automatically categorize your complaint and assign it
to the relevant department. You will receive further email updates when:
  - Your complaint is assigned to a department
  - The status changes to In Progress
  - Your complaint is Resolved, Closed, or Dumped

Thank you for reaching out.

Best regards,
Municipal Complaint System
                """
            },
            "complaint_categorized": {
                "subject": "Complaint Categorized - #{complaint_id}",
                "body": """
Dear {user_name},

Your complaint has been reviewed and categorized by our system.

--------------------------------------------------
Complaint ID   : {complaint_id}
Category       : {category}
Priority       : {priority}
Department     : {department}
--------------------------------------------------

Your complaint has been routed to the appropriate department and will
be assigned to an officer shortly. You will receive a notification
once it has been assigned.

Best regards,
Municipal Complaint System
                """
            },
            "complaint_assigned": {
                "subject": "Complaint Assigned - #{complaint_id}",
                "body": """
    Dear {user_name},

    Your complaint has been assigned to a department officer for resolution.

    --------------------------------------------------
    Complaint ID   : {complaint_id}
    Department     : {department}
    Assigned To    : {assigned_to}
    Category       : {category}
    Priority       : {priority}
    --------------------------------------------------

    The team will begin reviewing your complaint shortly.
    You will receive further updates as the status progresses.

    Best regards,
    Municipal Complaint System
                    """
                },
                "status_updated": {
                    "subject": "Complaint Status Update - #{complaint_id}",
                    "body": """
Dear {user_name},

{custom_message}

--------------------------------------------------
Complaint ID   : {complaint_id}
New Status     : {status}
--------------------------------------------------

Log in to your account to view full details.

Best regards,
Municipal Complaint System
                """
            },
            "department_alert": {
                "subject": "New Complaint Assignment - {category}",
                "body": """
                Dear Department Admin,
                
                A new complaint has been assigned to your department.
                
                Complaint ID: {complaint_id}
                Category: {category}
                Priority: {priority}
                Department: {department}
                
                Please review and take appropriate action.
                
                Best regards,
                Municipal Complaint System
                """
            }
        }
    
    async def send_email(self, to_email: str, subject: str, body: str = None, 
                        template_type: str = None, template_data: Dict = None):
        """Send email notification."""
        try:
            if not self.sender_email or not self.sender_password:
                logger.warning("Email credentials not configured. Skipping email send.")
                return False
            
            # Use template if provided
            if template_type and template_type in self.templates:
                template = self.templates[template_type]
                subject = template["subject"].format(**(template_data or {}))
                body = template["body"].format(**(template_data or {}))
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable security
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_bulk_email(self, recipients: list, subject: str, body: str):
        """Send email to multiple recipients."""
        results = []
        for recipient in recipients:
            result = await self.send_email(recipient, subject, body)
            results.append({"email": recipient, "sent": result})
        return results
    
    def get_available_templates(self):
        """Get list of available email templates."""
        return list(self.templates.keys())