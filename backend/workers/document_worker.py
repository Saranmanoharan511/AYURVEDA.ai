"""
Document Processing Worker

Background worker for processing uploaded documents through the document intelligence pipeline.
This worker polls the SQS document queue, processes documents using Textract, chunks them,
generates embeddings, and stores them in PostgreSQL with pgvector.

Pipeline:
1. Receive message from SQS
2. Download document from S3
3. Extract text using Textract
4. Chunk the extracted text
5. Generate embeddings for chunks
6. Store chunks in PostgreSQL with pgvector
7. Update document status to AVAILABLE_FOR_RAG
8. Handle failures with retry logic and dead-letter queue

Note: This is AWS Code-Only Mode. The worker code is written but actual
AWS SQS and S3 resources will be created manually after Sprint 8.
"""

import json
import time
import sys
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.services.sqs_service import sqs_service
from app.services.s3_service import s3_service
from app.services.textract_service import textract_service
from app.services.embedding_service import embedding_service
from app.services.chunking_service import chunking_service
from app.models.patient_document import PatientDocument
from app.models.report import Report
from app.models.document_chunk import DocumentChunk
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentProcessingWorker:
    """Worker for processing documents asynchronously."""
    
    def __init__(self):
        """Initialize the document worker with SQS and DLQ configuration."""
        self.region = settings.AWS_REGION
        self.queue_url = settings.SQS_DOCUMENT_QUEUE_URL
        self.dlq_url = settings.DLQ_DOCUMENT_QUEUE_URL
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY_SECONDS
        self.polling_interval = 20  # seconds
        self.running = False
        
        logger.info(f"Document Processing Worker initialized - Region: {self.region}, Queue: {self.queue_url}, DLQ: {self.dlq_url}")
    
    def start(self):
        """Start the document processing worker."""
        logger.info("Starting Document Processing Worker...")
        self.running = True
        
        try:
            while self.running:
                self.process_messages()
                time.sleep(self.polling_interval)
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            self.running = False
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            self.running = False
    
    def stop(self):
        """Stop the document processing worker."""
        logger.info("Stopping Document Processing Worker...")
        self.running = False
    
    def process_messages(self):
        """Process messages from the SQS document queue."""
        if not settings.SQS_DOCUMENT_QUEUE_URL:
            logger.warning("SQS_DOCUMENT_QUEUE_URL not configured. Skipping message processing.")
            return
        
        try:
            logger.debug(f"Polling SQS queue for messages (max 10, wait time 20s)")
            messages = sqs_service.receive_messages(
                queue_url=settings.SQS_DOCUMENT_QUEUE_URL,
                max_messages=10,
                wait_time=20
            )
            
            logger.info(f"Received {len(messages)} messages from SQS")
            
            for message in messages:
                try:
                    # Get approximate receive count from message attributes
                    receive_count = int(message.get('Attributes', {}).get('ApproximateReceiveCount', 0))
                    
                    # Check if max retries exceeded
                    if receive_count >= self.max_retries:
                        logger.warning(f"Message exceeded max retries ({self.max_retries}). Sending to DLQ.")
                        sent_to_dlq = self.send_to_dlq(message)
                        # Only delete from main queue if successfully sent to DLQ
                        if sent_to_dlq:
                            sqs_service.delete_message(
                                queue_url=settings.SQS_DOCUMENT_QUEUE_URL,
                                receipt_handle=message['ReceiptHandle']
                            )
                        else:
                            logger.error("WARNING: Message not sent to DLQ and will remain in queue for manual intervention.")
                        continue
                    
                    # Process the message
                    self.process_message(message)
                    
                    # Delete message after successful processing
                    sqs_service.delete_message(
                        queue_url=settings.SQS_DOCUMENT_QUEUE_URL,
                        receipt_handle=message['ReceiptHandle']
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    # Change visibility timeout to allow retry after delay
                    try:
                        sqs_service.change_message_visibility(
                            queue_url=settings.SQS_DOCUMENT_QUEUE_URL,
                            receipt_handle=message['ReceiptHandle'],
                            visibility_timeout=self.retry_delay
                        )
                    except Exception as visibility_error:
                        logger.error(f"Failed to change message visibility: {str(visibility_error)}")
                    
        except Exception as e:
            logger.error(f"Error receiving messages: {str(e)}")
    
    def send_to_dlq(self, message: Dict[str, Any]) -> bool:
        """Send failed message to dead-letter queue.
        
        Returns:
            True if message was successfully sent to DLQ, False otherwise
        """
        if not self.dlq_url:
            logger.error("DLQ URL not configured. Message will remain in main queue for manual intervention.")
            return False
        
        try:
            sqs_service.send_to_dlq(
                queue_url=self.dlq_url,
                message_body=message['Body'],
                message_attributes=message.get('MessageAttributes', {})
            )
            logger.info("Message sent to DLQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {str(e)}")
            return False
    
    def is_document_already_processed(self, document_id: str, document_source: str = "patient_document") -> bool:
        """
        Check if a document has already been processed.
        
        Args:
            document_id: UUID of the document
            document_source: Source of document ("patient_document" or "report")
            
        Returns:
            True if document is already processed, False otherwise
        """
        db = SessionLocal()
        try:
            logger.debug(f"Checking if document {document_id} (source: {document_source}) is already processed")
            
            if document_source == "report":
                document = db.query(Report).filter(
                    Report.id == document_id
                ).first()
            else:
                document = db.query(PatientDocument).filter(
                    PatientDocument.id == document_id
                ).first()
            
            if not document:
                logger.debug(f"Document {document_id} not found")
                return False
            
            # Document is considered processed if status is AVAILABLE_FOR_RAG
            is_processed = document.processing_status == 'AVAILABLE_FOR_RAG'
            logger.debug(f"Document {document_id} processing status: {document.processing_status}, is_processed: {is_processed}")
            
            return is_processed
        finally:
            db.close()
    
    def process_message(self, message: Dict[str, Any]):
        """Process a single document processing message."""
        try:
            body = json.loads(message['Body'])
            document_id = body.get('document_id')
            patient_id = body.get('patient_id')
            s3_object_key = body.get('s3_object_key')
            document_type = body.get('document_type')
            consultation_id = body.get('consultation_id')
            document_source = body.get('document_source', 'patient_document')
            
            logger.info(f"Processing document: {document_id} (source: {document_source}, type: {document_type}, patient: {patient_id})")
            
            # Idempotency check: Skip if document is already processed
            if self.is_document_already_processed(document_id, document_source):
                logger.info(f"Document {document_id} already processed. Skipping.")
                return
            
            # Update document status to PROCESSING
            logger.info(f"Updating document {document_id} status to PROCESSING")
            self.update_document_status(document_id, 'PROCESSING', document_source)
            
            # Process the document
            logger.info(f"Starting document processing pipeline for {document_id}")
            self.process_document(
                document_id=document_id,
                patient_id=patient_id,
                s3_object_key=s3_object_key,
                document_type=document_type,
                consultation_id=consultation_id,
                document_source=document_source
            )
            
            # Update document status to AVAILABLE_FOR_RAG
            logger.info(f"Updating document {document_id} status to AVAILABLE_FOR_RAG")
            self.update_document_status(document_id, 'AVAILABLE_FOR_RAG', document_source)
            
            logger.info(f"Successfully processed document: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to process document: {str(e)}")
            # Update document status to FAILED
            try:
                body_data = json.loads(message['Body'])
                document_id = body_data.get('document_id')
                document_source = body_data.get('document_source', 'patient_document')
                self.update_document_status(document_id, 'FAILED', document_source, error_message=str(e))
            except:
                pass
            raise
    
    def process_document(
        self,
        document_id: str,
        patient_id: str,
        s3_object_key: str,
        document_type: str,
        consultation_id: Optional[str] = None,
        document_source: str = "patient_document"
    ):
        """
        Process a document through the full pipeline.
        
        Args:
            document_id: UUID of the document
            patient_id: UUID of the patient
            s3_object_key: S3 object key of the document
            document_type: Type of document
            consultation_id: Optional consultation ID
            document_source: Source of document ("patient_document" or "report")
        """
        db = SessionLocal()
        
        try:
            logger.info(f"Starting document processing pipeline for {document_id}")
            
            # Get document record based on source
            if document_source == "report":
                document = db.query(Report).filter(
                    Report.id == document_id
                ).first()
            else:
                document = db.query(PatientDocument).filter(
                    PatientDocument.id == document_id
                ).first()
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                raise ValueError(f"Document not found: {document_id}")
            
            logger.info(f"Found document record: {document.original_filename}")
            
            # Step 1: Extract text from document using Textract
            logger.info(f"Step 1: Extracting text from document: {s3_object_key}")
            extracted_text = self.extract_document_text(s3_object_key)
            
            if not extracted_text:
                logger.error("Failed to extract text from document")
                raise ValueError("Failed to extract text from document")
            
            logger.info(f"Step 1 complete: Extracted {len(extracted_text)} characters from document")
            
            # Step 2: Chunk the extracted text
            logger.info("Step 2: Chunking document text...")
            chunks_data = chunking_service.chunk_text(
                text=extracted_text,
                metadata={
                    'document_id': document_id,
                    'patient_id': patient_id,
                    'consultation_id': consultation_id,
                    'document_type': document_type,
                    'source_filename': document.original_filename
                }
            )
            
            logger.info(f"Step 2 complete: Created {len(chunks_data)} chunks")
            
            # Step 3: Generate embeddings for chunks
            logger.info("Step 3: Generating embeddings for chunks...")
            chunk_texts = [chunk['chunk_text'] for chunk in chunks_data]
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
            
            successful_embeddings = len([e for e in embeddings if e])
            logger.info(f"Step 3 complete: Generated {successful_embeddings}/{len(chunks_data)} embeddings")
            
            # Step 4: Store chunks in database
            logger.info("Step 4: Storing chunks in database...")
            chunks_created = 0
            embeddings_generated = 0
            
            for i, chunk_data in enumerate(chunks_data):
                chunk = DocumentChunk(
                    document_id=document_id,
                    patient_id=patient_id,
                    consultation_id=consultation_id,
                    chunk_index=chunk_data['chunk_index'],
                    chunk_text=chunk_data['chunk_text'],
                    embedding=embeddings[i] if embeddings and embeddings[i] else None,
                    embedding_vector=embeddings[i] if embeddings and embeddings[i] else None,
                    chunk_metadata=chunk_data.get('metadata'),
                    source_filename=document.original_filename,
                    document_type=document_type
                )
                
                db.add(chunk)
                chunks_created += 1
                if embeddings and embeddings[i]:
                    embeddings_generated += 1
            
            db.commit()
            
            logger.info(f"Step 4 complete: Stored {chunks_created} chunks with {embeddings_generated} embeddings in database")
            logger.info(f"Document processing pipeline completed successfully for {document_id}")
            
        except Exception as e:
            logger.error(f"Document processing failed for {document_id}: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def extract_document_text(self, s3_object_key: str) -> Optional[str]:
        """
        Extract text from a document using Textract.
        
        Args:
            s3_object_key: S3 object key of the document
            
        Returns:
            Extracted text, None if extraction fails
        """
        try:
            logger.debug(f"Attempting Textract extraction for {s3_object_key}")
            # For text-based PDFs, we might need to download and extract differently
            # For now, use Textract for all documents
            extracted_text = textract_service.extract_text_from_document(
                s3_bucket=settings.S3_BUCKET_NAME,
                s3_object_key=s3_object_key
            )
            
            if extracted_text:
                logger.debug(f"Textract extraction successful for {s3_object_key}")
            
            return extracted_text
            
        except Exception as e:
            logger.warning(f"Textract extraction failed for {s3_object_key}: {str(e)}, trying fallback method")
            # Fallback: try to download and extract text directly
            return self.extract_text_directly(s3_object_key)
    
    def extract_text_directly(self, s3_object_key: str) -> Optional[str]:
        """
        Fallback method to extract text directly from S3.
        This attempts to download the file and extract text using local libraries.
        
        Args:
            s3_object_key: S3 object key of the document
            
        Returns:
            Extracted text, None if extraction fails
        """
        try:
            logger.debug(f"Attempting direct text extraction for {s3_object_key}")
            # Download file from S3
            import tempfile
            import os
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
                
            try:
                # Download from S3
                logger.debug(f"Downloading {s3_object_key} from S3 to {temp_path}")
                s3_service.download_file_to_path(
                    object_key=s3_object_key,
                    file_path=temp_path
                )
                
                # Try to extract text based on file type
                if s3_object_key.lower().endswith('.pdf'):
                    logger.debug("Extracting text from PDF using local method")
                    extracted_text = self.extract_from_pdf(temp_path)
                elif s3_object_key.lower().endswith(('.txt', '.md')):
                    logger.debug("Extracting text from text file")
                    extracted_text = self.extract_from_text_file(temp_path)
                else:
                    logger.error(f"Unsupported file type for direct extraction: {s3_object_key}")
                    return None
                
                if extracted_text:
                    logger.debug(f"Direct extraction successful: {len(extracted_text)} characters extracted")
                
                return extracted_text if extracted_text else None
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                    
        except Exception as e:
            logger.error(f"Direct text extraction failed for {s3_object_key}: {str(e)}")
            return None
    
    def extract_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF file using PyPDF2.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text, None if extraction fails
        """
        try:
            try:
                import PyPDF2
            except ImportError:
                logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
                return None
            
            logger.debug(f"Extracting text from PDF: {file_path}")
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text.append(page.extract_text())
            
            extracted_text = '\n'.join(text) if text else None
            if extracted_text:
                logger.debug(f"PDF extraction successful: {len(extracted_text)} characters extracted")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {str(e)}")
            return None
    
    def extract_from_text_file(self, file_path: str) -> Optional[str]:
        """
        Extract text from plain text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Extracted text, None if extraction fails
        """
        try:
            logger.debug(f"Extracting text from file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                logger.debug(f"Text file extraction successful: {len(text)} characters")
                return text
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                logger.debug("UTF-8 decoding failed, trying latin-1 encoding")
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                    logger.debug(f"Text file extraction successful with latin-1: {len(text)} characters")
                    return text
            except Exception as e:
                logger.error(f"Text file extraction failed for {file_path}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Text file extraction failed for {file_path}: {str(e)}")
            return None
    
    def update_document_status(
        self,
        document_id: str,
        status: str,
        document_source: str = "patient_document",
        error_message: Optional[str] = None
    ):
        """
        Update the processing status of a document.
        
        Args:
            document_id: UUID of the document
            status: New processing status
            document_source: Source of document ("patient_document" or "report")
            error_message: Optional error message
        """
        db = SessionLocal()
        
        try:
            logger.debug(f"Updating document {document_id} status to {status} (source: {document_source})")
            
            # Get document based on source
            if document_source == "report":
                document = db.query(Report).filter(
                    Report.id == document_id
                ).first()
            else:
                document = db.query(PatientDocument).filter(
                    PatientDocument.id == document_id
                ).first()
            
            if document:
                old_status = document.processing_status
                document.processing_status = status
                if error_message:
                    # Store error message in document_metadata if available
                    if hasattr(document, 'document_metadata'):
                        if not document.document_metadata:
                            from sqlalchemy.dialects.postgresql import JSONB
                            document.document_metadata = {}
                        document.document_metadata['error_message'] = error_message
                        document.document_metadata['error_timestamp'] = datetime.utcnow().isoformat()
                        logger.error(f"Document {document_id} error: {error_message}")
                
                db.commit()
                logger.info(f"Document {document_id} status updated: {old_status} -> {status}")
            else:
                logger.warning(f"Document {document_id} not found for status update")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update document status for {document_id}: {str(e)}")
        finally:
            db.close()


def main():
    """Main entry point for the document processing worker."""
    logger.info("Document Processing Worker main entry point called")
    worker = DocumentProcessingWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        worker.stop()
    except Exception as e:
        logger.error(f"Worker crashed: {str(e)}")
        worker.stop()


if __name__ == "__main__":
    main()
