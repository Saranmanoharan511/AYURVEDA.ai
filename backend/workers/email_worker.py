"""
Email Worker

Background worker script for processing email messages from SQS queue.
This worker listens to the SQS email queue and sends emails via SES.
"""

import sys
import os
# Add parent directory to path to import app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import logging
import time
from typing import Dict, Any
from app.services.sqs_service import sqs_service
from app.services.ses_service import ses_service
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_email_message(message_body: Dict[str, Any]) -> bool:
    """
    Process an email message from SQS.
    
    Args:
        message_body: Parsed message body from SQS
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user_id = message_body.get('user_id')
        event_type = message_body.get('event_type')
        recipient_email = message_body.get('recipient_email')
        subject = message_body.get('subject')
        body = message_body.get('body')
        metadata = message_body.get('metadata', {})
        
        logger.info(f"Processing email for user {user_id}, event type: {event_type}")
        
        # Send email based on event type
        if event_type == 'CONSULTATION_BOOKED':
            patient_name = metadata.get('patient_name', 'Patient')
            consultation_id = metadata.get('consultation_id')
            reason = metadata.get('reason')
            ses_service.send_consultation_booking_email(
                to_email=recipient_email,
                patient_name=patient_name,
                consultation_id=consultation_id,
                reason=reason
            )
        elif event_type == 'MEETING_SCHEDULED':
            patient_name = metadata.get('patient_name', 'Patient')
            doctor_name = metadata.get('doctor_name', 'Doctor')
            scheduled_date = metadata.get('scheduled_date')
            scheduled_time = metadata.get('scheduled_time')
            timezone = metadata.get('timezone')
            zoom_meeting_url = metadata.get('zoom_meeting_url')
            ses_service.send_meeting_scheduled_email(
                to_email=recipient_email,
                patient_name=patient_name,
                doctor_name=doctor_name,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                timezone=timezone,
                zoom_meeting_url=zoom_meeting_url
            )
        elif event_type == 'REPORT_UPLOADED':
            patient_name = metadata.get('patient_name', 'Patient')
            doctor_name = metadata.get('doctor_name', 'Doctor')
            report_type = metadata.get('report_type')
            report_filename = metadata.get('report_filename')
            ses_service.send_report_uploaded_email(
                to_email=recipient_email,
                patient_name=patient_name,
                doctor_name=doctor_name,
                report_type=report_type,
                report_filename=report_filename
            )
        else:
            # Generic email for other event types
            ses_service.send_email(
                to_email=recipient_email,
                subject=subject,
                body_html=body,
                body_text=body
            )
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to process email message: {str(e)}")
        return False


def run_email_worker():
    """
    Run the email worker to process messages from SQS queue.
    This function runs in a continuous loop, polling the SQS queue for messages.
    """
    logger.info("Starting email worker...")
    
    if not settings.SQS_EMAIL_QUEUE_URL:
        logger.error("SQS_EMAIL_QUEUE_URL not configured. Worker cannot start.")
        return
    
    while True:
        try:
            # Receive messages from SQS
            messages = sqs_service.receive_messages(
                queue_url=settings.SQS_EMAIL_QUEUE_URL,
                max_messages=10,
                wait_time=20
            )
            
            if messages:
                logger.info(f"Received {len(messages)} messages from SQS")
                
                for message in messages:
                    try:
                        # Parse message body
                        message_body = json.loads(message['Body'])
                        
                        # Process the message
                        success = process_email_message(message_body)
                        
                        if success:
                            # Delete message from queue if processed successfully
                            sqs_service.delete_message(
                                queue_url=settings.SQS_EMAIL_QUEUE_URL,
                                receipt_handle=message['ReceiptHandle']
                            )
                            logger.info(f"Message deleted from queue")
                        else:
                            logger.error(f"Failed to process message, leaving in queue for retry")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message body: {str(e)}")
                        # Delete malformed message
                        sqs_service.delete_message(
                            queue_url=settings.SQS_EMAIL_QUEUE_URL,
                            receipt_handle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        # Leave message in queue for retry
            else:
                logger.debug("No messages received from SQS")
                
        except Exception as e:
            logger.error(f"Error in email worker loop: {str(e)}")
            # Wait before retrying
            time.sleep(5)


if __name__ == "__main__":
    try:
        run_email_worker()
    except KeyboardInterrupt:
        logger.info("Email worker stopped by user")
    except Exception as e:
        logger.error(f"Email worker crashed: {str(e)}")
        raise
