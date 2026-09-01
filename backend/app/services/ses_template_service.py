"""
SES Email Template Service

This service manages Amazon SES email templates for the Ayurveda AI Platform.
It provides CRUD operations for email templates used in notifications.

AWS Code-Only Mode: This code integrates with SES but does not create
SES resources. The actual SES templates must be created manually.
"""

import boto3
from typing import Dict, List, Optional
from app.core.config import settings


class SESTemplateService:
    """Service for managing SES email templates."""

    def __init__(self):
        """Initialize SES client."""
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.SES_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID if hasattr(settings, 'AWS_ACCESS_KEY_ID') else None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') else None,
        )

    def create_template(
        self,
        template_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """
        Create a new SES email template.

        Args:
            template_name: Unique name for the template
            subject: Email subject line
            html_body: HTML content of the email
            text_body: Plain text content of the email (optional)

        Returns:
            Response from SES API

        Raises:
            Exception: If template creation fails
        """
        try:
            template_data = {
                'TemplateName': template_name,
                'SubjectPart': subject,
                'HtmlPart': html_body,
            }

            if text_body:
                template_data['TextPart'] = text_body

            response = self.ses_client.create_template(Template=template_data)
            return response

        except Exception as e:
            raise Exception(f"Failed to create SES template: {str(e)}")

    def update_template(
        self,
        template_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """
        Update an existing SES email template.

        Args:
            template_name: Name of the template to update
            subject: New email subject line
            html_body: New HTML content of the email
            text_body: New plain text content of the email (optional)

        Returns:
            Response from SES API

        Raises:
            Exception: If template update fails
        """
        try:
            template_data = {
                'TemplateName': template_name,
                'SubjectPart': subject,
                'HtmlPart': html_body,
            }

            if text_body:
                template_data['TextPart'] = text_body

            response = self.ses_client.update_template(Template=template_data)
            return response

        except Exception as e:
            raise Exception(f"Failed to update SES template: {str(e)}")

    def delete_template(self, template_name: str) -> Dict:
        """
        Delete an SES email template.

        Args:
            template_name: Name of the template to delete

        Returns:
            Response from SES API

        Raises:
            Exception: If template deletion fails
        """
        try:
            response = self.ses_client.delete_template(TemplateName=template_name)
            return response

        except Exception as e:
            raise Exception(f"Failed to delete SES template: {str(e)}")

    def get_template(self, template_name: str) -> Dict:
        """
        Retrieve an SES email template.

        Args:
            template_name: Name of the template to retrieve

        Returns:
            Template data including subject, HTML, and text parts

        Raises:
            Exception: If template retrieval fails
        """
        try:
            response = self.ses_client.get_template(TemplateName=template_name)
            return response['Template']

        except Exception as e:
            raise Exception(f"Failed to get SES template: {str(e)}")

    def list_templates(self) -> List[Dict]:
        """
        List all SES email templates.

        Returns:
            List of template metadata

        Raises:
            Exception: If template listing fails
        """
        try:
            response = self.ses_client.list_templates()
            return response['TemplatesMetadata']

        except Exception as e:
            raise Exception(f"Failed to list SES templates: {str(e)}")

    def send_templated_email(
        self,
        template_name: str,
        source_email: str,
        destination: Dict,
        template_data: Dict
    ) -> Dict:
        """
        Send an email using a template.

        Args:
            template_name: Name of the template to use
            source_email: Source email address
            destination: Destination addresses (To, Cc, Bcc)
            template_data: Data to substitute in the template

        Returns:
            Response from SES API

        Raises:
            Exception: If email sending fails
        """
        try:
            response = self.ses_client.send_templated_email(
                Source=source_email,
                Destination=destination,
                Template=template_name,
                TemplateData=str(template_data)
            )
            return response

        except Exception as e:
            raise Exception(f"Failed to send templated email: {str(e)}")


# Create singleton instance
ses_template_service = SESTemplateService()
