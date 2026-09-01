"""
Document Processing Schemas

Pydantic schemas for document processing operations including:
- Document chunking
- Embedding generation
- RAG retrieval
- Document search and filtering
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Document Chunk Schemas
class DocumentChunkCreate(BaseModel):
    """Schema for creating a document chunk."""
    document_id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID] = None
    chunk_index: int = Field(..., description="Index of the chunk within the document")
    chunk_text: str = Field(..., description="Text content of the chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    source_filename: Optional[str] = Field(None, description="Original filename")
    document_type: str = Field(..., description="Type of document")


class DocumentChunkUpdate(BaseModel):
    """Schema for updating a document chunk."""
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""
    id: UUID
    document_id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    chunk_index: int
    chunk_text: str
    embedding: Optional[List[float]]
    metadata: Optional[Dict[str, Any]]
    source_filename: Optional[str]
    document_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Embedding Schemas
class EmbeddingRequest(BaseModel):
    """Schema for embedding generation request."""
    text: str = Field(..., description="Text to generate embedding for")


class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""
    embedding: List[float] = Field(..., description="Vector embedding")
    model: str = Field(..., description="Model used for embedding generation")
    dimensions: int = Field(..., description="Dimensions of the embedding")


# Document Processing Schemas
class DocumentProcessingRequest(BaseModel):
    """Schema for document processing request (from SQS)."""
    document_id: UUID
    patient_id: UUID
    s3_object_key: str
    document_type: str
    consultation_id: Optional[UUID] = None


class DocumentProcessingStatus(BaseModel):
    """Schema for document processing status."""
    document_id: UUID
    processing_status: str = Field(..., description="Current processing status")
    chunks_created: int = Field(0, description="Number of chunks created")
    embeddings_generated: int = Field(0, description="Number of embeddings generated")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# RAG Retrieval Schemas
class RAGRetrievalRequest(BaseModel):
    """Schema for RAG retrieval request."""
    query: str = Field(..., description="Query text to search for")
    patient_id: UUID = Field(..., description="Patient ID for authorization filtering")
    consultation_id: Optional[UUID] = Field(None, description="Optional consultation ID filter")
    document_type: Optional[str] = Field(None, description="Optional document type filter")
    top_k: int = Field(5, description="Number of top results to return")
    min_similarity: float = Field(0.7, description="Minimum similarity threshold")


class RAGRetrievalResult(BaseModel):
    """Schema for RAG retrieval result."""
    chunk_id: UUID
    document_id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    chunk_index: int
    chunk_text: str
    similarity_score: float = Field(..., description="Similarity score")
    metadata: Optional[Dict[str, Any]]
    source_filename: Optional[str]
    document_type: str


class RAGRetrievalResponse(BaseModel):
    """Schema for RAG retrieval response."""
    query: str
    results: List[RAGRetrievalResult]
    total_results: int


# Document Search Schemas
class DocumentSearchRequest(BaseModel):
    """Schema for document search request."""
    patient_id: Optional[UUID] = Field(None, description="Filter by patient ID")
    consultation_id: Optional[UUID] = Field(None, description="Filter by consultation ID")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    processing_status: Optional[str] = Field(None, description="Filter by processing status")
    search_text: Optional[str] = Field(None, description="Search in filename or metadata")
    limit: int = Field(50, description="Maximum number of results")
    offset: int = Field(0, description="Offset for pagination")


class DocumentSearchResult(BaseModel):
    """Schema for document search result."""
    id: UUID
    patient_id: UUID
    consultation_id: Optional[UUID]
    document_type: str
    original_filename: str
    upload_status: str
    processing_status: str
    created_at: datetime
    chunk_count: Optional[int] = Field(None, description="Number of chunks created")


class DocumentSearchResponse(BaseModel):
    """Schema for document search response."""
    results: List[DocumentSearchResult]
    total_count: int
    limit: int
    offset: int


# Chunking Configuration Schema
class ChunkingConfig(BaseModel):
    """Schema for document chunking configuration."""
    chunk_size: int = Field(1000, description="Maximum chunk size in characters")
    chunk_overlap: int = Field(200, description="Overlap between chunks in characters")
    min_chunk_size: int = Field(100, description="Minimum chunk size in characters")
    preserve_newlines: bool = Field(True, description="Preserve newlines in chunks")
