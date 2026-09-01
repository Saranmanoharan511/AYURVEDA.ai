"""
Document Chunk Model

This module defines the DocumentChunk SQLAlchemy model for the document_chunks table.
The document_chunks table stores processed document chunks with vector embeddings
for semantic search and RAG (Retrieval-Augmented Generation).

Table Schema:
- id: UUID primary key
- document_id: Foreign key to patient_documents table
- patient_id: Foreign key to patients table (for authorization)
- consultation_id: Foreign key to consultations table (optional)
- chunk_index: Index of the chunk within the document
- chunk_text: Text content of the chunk
- embedding: Vector embedding array (pgvector)
- metadata: JSONB metadata (document type, source, etc.)
- source_filename: Original filename of the source document
- document_type: Type of document (medical_report, prescription, etc.)
- created_at: Timestamp when chunk was created
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid
from app.db.session import Base
from app.core.config import settings

# Try to import pgvector type if available
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback to ARRAY(Float) if pgvector is not installed
    Vector = None


class DocumentChunk(Base):
    """DocumentChunk model for storing processed document chunks with embeddings."""
    
    __tablename__ = "document_chunks"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    consultation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Chunk information
    chunk_index = Column(Integer(), nullable=False)
    chunk_text = Column(Text(), nullable=False)
    
    # Vector embedding (pgvector)
    embedding = Column(ARRAY(Float), nullable=True)  # Fallback for environments without pgvector
    # embedding_vector column added after class definition based on pgvector availability
    
    # Metadata and source information (renamed to avoid reserved name)
    chunk_metadata = Column(JSONB(), nullable=True)
    source_filename = Column(String(255), nullable=True)
    document_type = Column(String(100), nullable=False, index=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
    
    def to_dict(self):
        """Convert document chunk object to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "patient_id": str(self.patient_id),
            "consultation_id": str(self.consultation_id) if self.consultation_id else None,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "embedding": self.embedding.tolist() if self.embedding else None,
            "chunk_metadata": self.chunk_metadata,
            "source_filename": self.source_filename,
            "document_type": self.document_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Add embedding_vector column based on pgvector availability
if PGVECTOR_AVAILABLE:
    DocumentChunk.embedding_vector = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)
else:
    DocumentChunk.embedding_vector = Column(ARRAY(Float), nullable=True)
