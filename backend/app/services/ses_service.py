"""
SES Service

Service for interacting with Amazon SES for sending transactional emails.
This service handles email sending for various events such as consultation bookings,
meeting schedules, report uploads, and follow-up reminders.
"""

import boto3
from typing import Optional, List
from app.core.config import settings


class SESService:
    """Service for interacting with Amazon SES."""
    
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.SES_REGION or settings.AWS_REGION
        )
        self.from_email = settings.SES_FROM_EMAIL
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Send an email using Amazon SES.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML body content
            body_text: Plain text body content (optional)
            
        Returns:
            Message ID if successful, None otherwise
            
        Raises:
            ValueError: If from email is not configured
        """
        if not self.from_email:
            raise ValueError("SES_FROM_EMAIL not configured")
        
        try:
            # Build email parameters
            email_params = {
                'Source': self.from_email,
                'Destination': {
                    'ToAddresses': [to_email]
                },
                'Message': {
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            }
            
            # Add plain text body if provided
            if body_text:
                email_params['Message']['Body']['Text'] = {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                }
            
            response = self.ses_client.send_email(**email_params)
            return response.get('MessageId')
        except Exception as e:
            raise Exception(f"Failed to send email via SES: {str(e)}")
    
    def send_consultation_booking_email(
        self,
        to_email: str,
        patient_name: str,
        consultation_id: str,
        reason: str
    ) -> Optional[str]:
        """
        Send consultation booking confirmation email.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            consultation_id: Consultation UUID
            reason: Consultation reason
            
        Returns:
            Message ID if successful
        """
        subject = "Consultation Booking Confirmed"
        
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h1>Consultation Booking Confirmed</h1>
            <p>Dear {patient_name},</p>
            <p>Your consultation has been successfully booked.</p>
            <p><strong>Consultation ID:</strong> {consultation_id}</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p>The doctor will review your request and schedule a meeting. You will receive another email with the meeting details.</p>
            <p>Thank you for choosing our Ayurveda consultation service.</p>
        </body>
        </html>
        """
        
        body_text = f"""
        Consultation Booking Confirmed
        
        Dear {patient_name},
        
        Your consultation has been successfully booked.
        
        Consultation ID: {consultation_id}
        Reason: {reason}
        
        The doctor will review your request and schedule a meeting. You will receive another email with the meeting details.
        
        Thank you for choosing our Ayurveda consultation service.
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_meeting_scheduled_email(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        scheduled_date: str,
        scheduled_time: str,
        timezone: str,
        zoom_meeting_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Send meeting scheduled email.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            doctor_name: Doctor name
            scheduled_date: Scheduled date
            scheduled_time: Scheduled time
            timezone: Timezone
            zoom_meeting_url: Zoom meeting URL (optional)
            
        Returns:
            Message ID if successful
        """
        subject = "Meeting Scheduled"
        
        zoom_link_html = f"<p><strong>Zoom Meeting Link:</strong> <a href='{zoom_meeting_url}'>{zoom_meeting_url}</a></p>" if zoom_meeting_url else ""
        zoom_link_text = f"\nZoom Meeting Link: {zoom_meeting_url}" if zoom_meeting_url else ""
        
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h1>Meeting Scheduled</h1>
            <p>Dear {patient_name},</p>
            <p>Your consultation meeting has been scheduled.</p>
            <p><strong>Doctor:</strong> {doctor_name}</p>
            <p><strong>Date:</strong> {scheduled_date}</p>
            <p><strong>Time:</strong> {scheduled_time} {timezone}</p>
            {zoom_link_html}
            <p>Please join the meeting at the scheduled time. If you have any questions, please contact us.</p>
            <p>Thank you.</p>
        </body>
        </html>
        """
        
        body_text = f"""
        Meeting Scheduled
        
        Dear {patient_name},
        
        Your consultation meeting has been scheduled.
        
        Doctor: {doctor_name}
        Date: {scheduled_date}
        Time: {scheduled_time} {timezone}
        {zoom_link_text}
        
        Please join the meeting at the scheduled time. If you have any questions, please contact us.
        
        Thank you.
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_report_uploaded_email(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        report_type: str,
        report_filename: str
    ) -> Optional[str]:
        """
        Send report uploaded email.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            doctor_name: Doctor name
            report_type: Type of report
            report_filename: Report filename
            
        Returns:
            Message ID if successful
        """
        subject = "Report Available"
        
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h1>Report Available</h1>
            <p>Dear {patient_name},</p>
            <p>Your doctor has uploaded a report for your consultation.</p>
            <p><strong>Doctor:</strong> {doctor_name}</p>
            <p><strong>Report Type:</strong> {report_type}</p>
            <p><strong>Report Filename:</strong> {report_filename}</p>
            <p>Please log in to your patient portal to view and download the report.</p>
            <p>Thank you.</p>
        </body>
        </html>
        """
        
        body_text = f"""
        Report Available
        
        Dear {patient_name},
        
        Your doctor has uploaded a report for your consultation.
        
        Doctor: {doctor_name}
        Report Type: {report_type}
        Report Filename: {report_filename}
        
        Please log in to your patient portal to view and download the report.
        
        Thank you.
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_documents_email(
        self,
        to_email: str,
        patient_name: str,
        doctor_name: str,
        consultation_id: str,
        report_attachments: List[dict],
        prescription_attachments: List[dict]
    ) -> Optional[str]:
        """
        Send email with reports and prescription PDFs attached.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            doctor_name: Doctor name
            consultation_id: Consultation UUID
            report_attachments: List of dicts with 'filename' and 'data' (bytes) for reports
            prescription_attachments: List of dicts with 'filename' and 'data' (bytes) for prescriptions
            
        Returns:
            Message ID if successful
        """
        subject = "Your Consultation Documents"
        
        # Build attachment list for email body
        report_list_html = ""
        report_list_text = ""
        if report_attachments:
            report_list_html = "<h3>Reports Attached:</h3><ul>"
            report_list_text = "\nReports Attached:\n"
            for report in report_attachments:
                report_list_html += f"<li>{report['filename']}</li>"
                report_list_text += f"- {report['filename']}\n"
            report_list_html += "</ul>"
        
        prescription_list_html = ""
        prescription_list_text = ""
        if prescription_attachments:
            prescription_list_html = "<h3>Prescriptions Attached:</h3><ul>"
            prescription_list_text = "\nPrescriptions Attached:\n"
            for prescription in prescription_attachments:
                prescription_list_html += f"<li>{prescription['filename']}</li>"
                prescription_list_text += f"- {prescription['filename']}\n"
            prescription_list_html += "</ul>"
        
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h1>Your Consultation Documents</h1>
            <p>Dear {patient_name},</p>
            <p>Your doctor, {doctor_name}, has sent you the following documents for your consultation.</p>
            <p><strong>Consultation ID:</strong> {consultation_id}</p>
            {report_list_html}
            {prescription_list_html}
            <p>Please find the documents attached to this email. If you have any questions about these documents, please contact your doctor or our support team.</p>
            <p>Thank you for choosing our Ayurveda consultation service.</p>
        </body>
        </html>
        """
        
        body_text = f"""
        Your Consultation Documents
        
        Dear {patient_name},
        
        Your doctor, {doctor_name}, has sent you the following documents for your consultation.
        
        Consultation ID: {consultation_id}
        {report_list_text}
        {prescription_list_text}
        Please find the documents attached to this email. If you have any questions about these documents, please contact your doctor or our support team.
        
        Thank you for choosing our Ayurveda consultation service.
        """
        
        try:
            # Build email with attachments using raw email
            import email
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            import base64
            
            # Create multipart message
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create alternative part for HTML and text
            alt_msg = MIMEMultipart('alternative')
            alt_part1 = MIMEText(body_text, 'plain', 'UTF-8')
            alt_part2 = MIMEText(body_html, 'html', 'UTF-8')
            alt_msg.attach(alt_part1)
            alt_msg.attach(alt_part2)
            msg.attach(alt_msg)
            
            # Attach reports
            for report in report_attachments:
                attachment = MIMEApplication(report['data'])
                attachment.add_header('Content-Disposition', 'attachment', filename=report['filename'])
                msg.attach(attachment)
            
            # Attach prescriptions
            for prescription in prescription_attachments:
                attachment = MIMEApplication(prescription['data'])
                attachment.add_header('Content-Disposition', 'attachment', filename=prescription['filename'])
                msg.attach(attachment)
            
            # Send raw email
            response = self.ses_client.send_raw_email(
                Source=self.from_email,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            return response.get('MessageId')
        except Exception as e:
            raise Exception(f"Failed to send email with attachments via SES: {str(e)}")


# Singleton instance
ses_service = SESService()
