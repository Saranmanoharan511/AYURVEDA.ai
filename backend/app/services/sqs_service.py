"""
SQS Service

Service for interacting with Amazon SQS for asynchronous background jobs.
This service handles sending messages to SQS queues for email processing
and other background tasks.
"""

import boto3
import json
import os
from typing import Optional, Dict, Any
from app.core.config import settings


class SQSService:
    """Service for interacting with Amazon SQS."""
    
    def __init__(self):
        self.sqs_client = boto3.client(
            'sqs',
            region_name=settings.AWS_REGION
        )
        self.email_queue_url = settings.SQS_EMAIL_QUEUE_URL
        self.document_queue_url = settings.SQS_DOCUMENT_QUEUE_URL
    
    def send_email_message(
        self,
        user_id: str,
        event_type: str,
        recipient_email: str,
        subject: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send an email message to the SQS email queue.
        
        Args:
            user_id: UUID of the user
            event_type: Type of event (e.g., CONSULTATION_BOOKED, MEETING_SCHEDULED)
            recipient_email: Email address of the recipient
            subject: Email subject line
            body: Email body content
            metadata: Additional metadata as a dictionary
            
        Returns:
            Message ID if successful, None otherwise
            
        Raises:
            ValueError: If queue URL is not configured
        """
        if not self.email_queue_url:
            raise ValueError("SQS_EMAIL_QUEUE_URL not configured")
        
        message_body = {
            "user_id": str(user_id),
            "event_type": event_type,
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
            "metadata": metadata or {}
        }
        
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.email_queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'EventType': {
                        'DataType': 'String',
                        'StringValue': event_type
                    }
                }
            )
            return response.get('MessageId')
        except Exception as e:
            raise Exception(f"Failed to send message to SQS: {str(e)}")
    
    def send_document_processing_message(
        self,
        document_id: str,
        patient_id: str,
        s3_object_key: str,
        document_type: str,
        consultation_id: Optional[str] = None,
        document_source: str = "patient_document"
    ) -> Optional[str]:
        """
        Send a document processing message to the SQS document queue.
        
        Args:
            document_id: UUID of the document
            patient_id: UUID of the patient
            s3_object_key: S3 object key of the document
            document_type: Type of document
            consultation_id: Optional consultation ID
            document_source: Source of document ("patient_document" or "report")
            
        Returns:
            Message ID if successful, None otherwise
            
        Raises:
            ValueError: If queue URL is not configured
        """
        if not self.document_queue_url:
            raise ValueError("SQS_DOCUMENT_QUEUE_URL not configured")
        
        message_body = {
            "document_id": str(document_id),
            "patient_id": str(patient_id),
            "s3_object_key": s3_object_key,
            "document_type": document_type,
            "consultation_id": str(consultation_id) if consultation_id else None,
            "document_source": document_source
        }
        
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.document_queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'DocumentType': {
                        'DataType': 'String',
                        'StringValue': document_type
                    },
                    'DocumentSource': {
                        'DataType': 'String',
                        'StringValue': document_source
                    }
                }
            )
            return response.get('MessageId')
        except Exception as e:
            raise Exception(f"Failed to send document processing message to SQS: {str(e)}")
    
    def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 10,
        wait_time: int = 20
    ) -> list:
        """
        Receive messages from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            max_messages: Maximum number of messages to retrieve (default: 10)
            wait_time: Long polling wait time in seconds (default: 20)
            
        Returns:
            List of messages
        """
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            return response.get('Messages', [])
        except Exception as e:
            raise Exception(f"Failed to receive messages from SQS: {str(e)}")
    
    def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """
        Delete a message from an SQS queue.
        
        Args:
            queue_url: URL of the SQS queue
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            True if successful
        """
        try:
            self.sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete message from SQS: {str(e)}")
    
    def change_message_visibility(
        self,
        queue_url: str,
        receipt_handle: str,
        visibility_timeout: int
    ) -> bool:
        """
        Change the visibility timeout of a message.
        This is used for retry logic - extend visibility during processing
        or make message visible again for retry.
        
        Args:
            queue_url: URL of the SQS queue
            receipt_handle: Receipt handle of the message
            visibility_timeout: New visibility timeout in seconds
            
        Returns:
            True if successful
        """
        try:
            self.sqs_client.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=visibility_timeout
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to change message visibility: {str(e)}")
    
    def send_to_dlq(
        self,
        queue_url: str,
        message_body: str,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send a message to a dead-letter queue.
        
        Args:
            queue_url: URL of the DLQ
            message_body: Message body as JSON string
            message_attributes: Optional message attributes
            
        Returns:
            Message ID if successful, None otherwise
        """
        try:
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_body,
                MessageAttributes=message_attributes or {}
            )
            return response.get('MessageId')
        except Exception as e:
            raise Exception(f"Failed to send message to DLQ: {str(e)}")


# Singleton instance
sqs_service = SQSService()
