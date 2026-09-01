import boto3
import os
from typing import Optional
from app.core.config import settings


class S3Service:
    """Service for interacting with Amazon S3 for document storage."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def generate_presigned_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for uploading a file to S3.
        
        Args:
            object_key: The key (path) where the file will be stored in S3
            content_type: The MIME type of the file
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for upload
            
        Raises:
            ValueError: If bucket name is not configured
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned upload URL: {str(e)}")
    
    def generate_presigned_download_url(
        self,
        object_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for downloading a file from S3.
        
        Args:
            object_key: The key (path) of the file in S3
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL for download
            
        Raises:
            ValueError: If bucket name is not configured
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned download URL: {str(e)}")
    
    def delete_object(self, object_key: str) -> bool:
        """
        Delete an object from S3.
        
        Args:
            object_key: The key (path) of the file in S3
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If bucket name is not configured
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete object: {str(e)}")
    
    def check_object_exists(self, object_key: str) -> bool:
        """
        Check if an object exists in S3.
        
        Args:
            object_key: The key (path) of the file in S3
            
        Returns:
            True if object exists, False otherwise
        """
        if not self.bucket_name:
            return False
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except self.s3_client.exceptions.ClientError:
            return False
    
    def upload_file(
        self,
        file_data: bytes,
        object_key: str,
        content_type: str
    ) -> bool:
        """
        Upload a file directly to S3.
        
        Args:
            file_data: The file data as bytes
            object_key: The key (path) where the file will be stored in S3
            content_type: The MIME type of the file
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If bucket name is not configured
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def download_file(self, object_key: str) -> bytes:
        """
        Download a file from S3.
        
        Args:
            object_key: The key (path) of the file in S3
            
        Returns:
            File data as bytes
            
        Raises:
            ValueError: If bucket name is not configured
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")


# Singleton instance
s3_service = S3Service()
