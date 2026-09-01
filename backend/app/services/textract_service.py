"""
Textract Service

Service for interacting with Amazon Textract for OCR and document extraction.
This service handles extracting text and structured data from scanned documents,
PDFs, and images using Amazon Textract.

Note: This is AWS Code-Only Mode. The service code is written but actual
AWS Textract resources will be created manually after Sprint 8.
"""

import boto3
import os
from typing import Optional, Dict, Any, List
from app.core.config import settings


class TextractService:
    """Service for interacting with Amazon Textract."""
    
    def __init__(self):
        self.textract_client = boto3.client(
            'textract',
            region_name=settings.AWS_REGION
        )
    
    def extract_text_from_document(
        self,
        s3_bucket: str,
        s3_object_key: str
    ) -> Optional[str]:
        """
        Extract text from a document stored in S3 using Amazon Textract.
        
        Args:
            s3_bucket: Name of the S3 bucket
            s3_object_key: S3 object key of the document
            
        Returns:
            Extracted text as a string, None if extraction fails
            
        Raises:
            ValueError: If S3 bucket name is not configured
            Exception: If Textract extraction fails
        """
        if not s3_bucket:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                }
            )
            
            # Extract text from Textract response
            extracted_text = []
            for block in response.get('Blocks', []):
                if block.get('BlockType') == 'LINE':
                    text = block.get('Text', '')
                    if text:
                        extracted_text.append(text)
            
            return '\n'.join(extracted_text)
            
        except Exception as e:
            raise Exception(f"Failed to extract text from document: {str(e)}")
    
    def extract_text_from_bytes(
        self,
        document_bytes: bytes
    ) -> Optional[str]:
        """
        Extract text from document bytes using Amazon Textract.
        
        Args:
            document_bytes: Raw bytes of the document
            
        Returns:
            Extracted text as a string, None if extraction fails
            
        Raises:
            Exception: If Textract extraction fails
        """
        try:
            response = self.textract_client.detect_document_text(
                Document={'Bytes': document_bytes}
            )
            
            # Extract text from Textract response
            extracted_text = []
            for block in response.get('Blocks', []):
                if block.get('BlockType') == 'LINE':
                    text = block.get('Text', '')
                    if text:
                        extracted_text.append(text)
            
            return '\n'.join(extracted_text)
            
        except Exception as e:
            raise Exception(f"Failed to extract text from document bytes: {str(e)}")
    
    def extract_structured_data(
        self,
        s3_bucket: str,
        s3_object_key: str,
        forms: bool = True,
        tables: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Extract structured data (forms and tables) from a document.
        
        Args:
            s3_bucket: Name of the S3 bucket
            s3_object_key: S3 object key of the document
            forms: Whether to extract form data
            tables: Whether to extract table data
            
        Returns:
            Dictionary containing extracted forms and tables
            
        Raises:
            ValueError: If S3 bucket name is not configured
            Exception: If Textract extraction fails
        """
        if not s3_bucket:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            feature_types = []
            if forms:
                feature_types.append('FORMS')
            if tables:
                feature_types.append('TABLES')
            
            if not feature_types:
                # If no features requested, just do basic text extraction
                return {
                    'text': self.extract_text_from_document(s3_bucket, s3_object_key),
                    'forms': {},
                    'tables': []
                }
            
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                },
                FeatureTypes=feature_types
            )
            
            result = {
                'forms': {},
                'tables': []
            }
            
            # Extract form data
            if forms:
                for block in response.get('Blocks', []):
                    if block.get('BlockType') == 'KEY_VALUE_SET':
                        if block.get('EntityTypes') == ['KEY']:
                            key = block.get('Text', '')
                            # Find the corresponding value
                            # (simplified implementation - in production, would need proper relationship mapping)
                            if key:
                                result['forms'][key] = ''
            
            # Extract table data
            if tables:
                tables_data = {}
                for block in response.get('Blocks', []):
                    if block.get('BlockType') == 'TABLE':
                        table_id = block.get('Id')
                        tables_data[table_id] = {'cells': []}
                    elif block.get('BlockType') == 'CELL':
                        table_id = block.get('Relationships', [{}])[0].get('Ids', [''])[0] if block.get('Relationships') else None
                        if table_id and table_id in tables_data:
                            tables_data[table_id]['cells'].append({
                                'row_index': block.get('RowIndex'),
                                'column_index': block.get('ColumnIndex'),
                                'text': block.get('Text', '')
                            })
                
                result['tables'] = list(tables_data.values())
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to extract structured data from document: {str(e)}")
    
    def start_async_extraction(
        self,
        s3_bucket: str,
        s3_object_key: str
    ) -> Optional[str]:
        """
        Start asynchronous document extraction for large documents.
        
        Args:
            s3_bucket: Name of the S3 bucket
            s3_object_key: S3 object key of the document
            
        Returns:
            Job ID for the asynchronous extraction
            
        Raises:
            ValueError: If S3 bucket name is not configured
            Exception: If Textract job submission fails
        """
        if not s3_bucket:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            response = self.textract_client.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_object_key
                    }
                }
            )
            
            return response.get('JobId')
            
        except Exception as e:
            raise Exception(f"Failed to start async extraction: {str(e)}")
    
    def get_extraction_results(
        self,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get results of an asynchronous extraction job.
        
        Args:
            job_id: Job ID from start_async_extraction
            
        Returns:
            Extraction results or status
            
        Raises:
            Exception: If Textract job retrieval fails
        """
        try:
            response = self.textract_client.get_document_text_detection(JobId=job_id)
            
            job_status = response.get('JobStatus')
            
            if job_status == 'SUCCEEDED':
                # Extract text from results
                extracted_text = []
                for block in response.get('Blocks', []):
                    if block.get('BlockType') == 'LINE':
                        text = block.get('Text', '')
                        if text:
                            extracted_text.append(text)
                
                return {
                    'status': 'SUCCEEDED',
                    'text': '\n'.join(extracted_text)
                }
            elif job_status == 'FAILED':
                return {
                    'status': 'FAILED',
                    'error': response.get('StatusMessage', 'Unknown error')
                }
            else:
                return {
                    'status': job_status
                }
                
        except Exception as e:
            raise Exception(f"Failed to get extraction results: {str(e)}")


# Singleton instance
textract_service = TextractService()
