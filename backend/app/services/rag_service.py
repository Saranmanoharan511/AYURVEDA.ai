"""
RAG Service

Service for Retrieval-Augmented Generation (RAG) with patient-aware retrieval.
This service handles semantic search over document chunks using pgvector,
with strict enforcement of patient authorization boundaries.

Key Features:
- Patient-scoped retrieval (WHERE patient_id = authorized_patient_id)
- Consultation filtering
- Document type filtering
- Vector similarity search using pgvector
- Authorization enforcement
- Source reference tracking
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.sql import text
from app.services.embedding_service import embedding_service
from app.models.document_chunk import DocumentChunk
from app.schemas.document_processing import RAGRetrievalRequest, RAGRetrievalResult, RAGRetrievalResponse


class RAGService:
    """Service for RAG retrieval with patient authorization."""
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        patient_id: str,
        db: Session,
        consultation_id: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> RAGRetrievalResponse:
        """
        Retrieve relevant document chunks for a query with patient authorization.
        
        Args:
            query: Query text to search for
            patient_id: Patient ID for authorization filtering (CRITICAL)
            db: Database session
            consultation_id: Optional consultation ID filter
            document_type: Optional document type filter
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            RAGRetrievalResponse with relevant chunks
            
        Raises:
            ValueError: If query is empty or patient_id is not provided
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not patient_id:
            raise ValueError("Patient ID is required for authorization")
        
        # Generate embedding for the query
        query_embedding = self.embedding_service.generate_embedding(query)
        
        if not query_embedding:
            raise ValueError("Failed to generate query embedding")
        
        # Build the base query with patient authorization filter
        # CRITICAL: Always filter by patient_id to prevent cross-patient retrieval
        base_query = db.query(DocumentChunk).filter(
            DocumentChunk.patient_id == patient_id
        )
        
        # Add optional filters
        if consultation_id:
            base_query = base_query.filter(
                DocumentChunk.consultation_id == consultation_id
            )
        
        if document_type:
            base_query = base_query.filter(
                DocumentChunk.document_type == document_type
            )
        
        # Only retrieve chunks that have embeddings
        base_query = base_query.filter(
            DocumentChunk.embedding.isnot(None)
        )
        
        # Try to use pgvector vector similarity search if available
        try:
            # Check if embedding_vector column exists
            db.execute(text("SELECT embedding_vector FROM document_chunks LIMIT 1"))
            
            # Use pgvector cosine similarity search
            # Convert embedding array to vector format for pgvector
            embedding_array_str = f"[{','.join(str(x) for x in query_embedding)}]"
            
            similarity_expr = text(
                "1 - (embedding_vector <=> :query_embedding::vector)"
            ).bindparams(query_embedding=embedding_array_str)
            
            results = base_query.add_columns(
                similarity_expr.label('similarity')
            ).order_by(
                text('similarity DESC')
            ).limit(top_k).all()
            
            # Filter by minimum similarity
            results = [r for r in results if r.similarity >= min_similarity]
            
        except Exception:
            # Fall back to keyword-based retrieval if pgvector not available
            keyword_conditions = []
            query_words = query.lower().split()
            for word in query_words:
                if len(word) > 3:  # Only meaningful words
                    keyword_conditions.append(
                        DocumentChunk.chunk_text.ilike(f'%{word}%')
                    )
            
            if keyword_conditions:
                base_query = base_query.filter(
                    or_(*keyword_conditions)
                )
            
            # Order by creation date (most recent first) and limit
            results = base_query.order_by(
                DocumentChunk.created_at.desc()
            ).limit(top_k).all()
        
        # Convert results to RAGRetrievalResult objects
        retrieval_results = []
        for result in results:
            # Handle different result types:
            # 1. SQLAlchemy 2.0 Row objects from add_columns() (with similarity as attribute)
            # 2. Tuple results (chunk, similarity)
            # 3. Plain chunk objects (keyword match)
            
            if hasattr(result, 'similarity'):
                # SQLAlchemy 2.0 Row object from add_columns()
                # The chunk is the first element or accessible via DocumentChunk
                if hasattr(result, 'DocumentChunk'):
                    chunk = result.DocumentChunk
                else:
                    chunk = result[0]
                similarity = result.similarity
            elif isinstance(result, tuple):
                # Tuple result (chunk, similarity)
                chunk = result[0]
                similarity = result[1] if len(result) > 1 else 0.8
            else:
                # Plain chunk object (keyword match)
                chunk = result
                similarity = 0.8  # Default score for keyword match
            
            retrieval_results.append(RAGRetrievalResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                patient_id=chunk.patient_id,
                consultation_id=chunk.consultation_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                similarity_score=similarity,
                metadata=chunk.chunk_metadata,
                source_filename=chunk.source_filename,
                document_type=chunk.document_type
            ))
        
        return RAGRetrievalResponse(
            query=query,
            results=retrieval_results,
            total_results=len(retrieval_results)
        )
    
    def retrieve_by_keywords(
        self,
        keywords: List[str],
        patient_id: str,
        db: Session,
        consultation_id: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: int = 5
    ) -> RAGRetrievalResponse:
        """
        Retrieve document chunks by keyword matching with patient authorization.
        
        Args:
            keywords: List of keywords to search for
            patient_id: Patient ID for authorization filtering (CRITICAL)
            db: Database session
            consultation_id: Optional consultation ID filter
            document_type: Optional document type filter
            top_k: Number of top results to return
            
        Returns:
            RAGRetrievalResponse with matching chunks
        """
        if not keywords:
            raise ValueError("Keywords cannot be empty")
        
        if not patient_id:
            raise ValueError("Patient ID is required for authorization")
        
        # Build query with patient authorization filter
        # CRITICAL: Always filter by patient_id
        base_query = db.query(DocumentChunk).filter(
            DocumentChunk.patient_id == patient_id
        )
        
        # Add optional filters
        if consultation_id:
            base_query = base_query.filter(
                DocumentChunk.consultation_id == consultation_id
            )
        
        if document_type:
            base_query = base_query.filter(
                DocumentChunk.document_type == document_type
            )
        
        # Add keyword matching using ILIKE (case-insensitive)
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.append(
                DocumentChunk.chunk_text.ilike(f'%{keyword}%')
            )
        
        if keyword_conditions:
            base_query = base_query.filter(
                or_(*keyword_conditions)
            )
        
        # Order by creation date (most recent first) and limit
        results = base_query.order_by(
            DocumentChunk.created_at.desc()
        ).limit(top_k).all()
        
        # Convert results to RAGRetrievalResult objects
        retrieval_results = []
        for chunk in results:
            retrieval_results.append(RAGRetrievalResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                patient_id=chunk.patient_id,
                consultation_id=chunk.consultation_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                similarity_score=1.0,  # Perfect match for keyword search
                metadata=chunk.chunk_metadata,
                source_filename=chunk.source_filename,
                document_type=chunk.document_type
            ))
        
        return RAGRetrievalResponse(
            query=' '.join(keywords),
            results=retrieval_results,
            total_results=len(retrieval_results)
        )
    
    def get_patient_context(
        self,
        patient_id: str,
        db: Session,
        consultation_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get a comprehensive context for a patient including all document chunks.
        
        Args:
            patient_id: Patient ID for authorization filtering (CRITICAL)
            db: Database session
            consultation_id: Optional consultation ID filter
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List of document chunks for patient context
        """
        if not patient_id:
            raise ValueError("Patient ID is required for authorization")
        
        # Build query with patient authorization filter
        # CRITICAL: Always filter by patient_id
        base_query = db.query(DocumentChunk).filter(
            DocumentChunk.patient_id == patient_id
        )
        
        # Add optional consultation filter
        if consultation_id:
            base_query = base_query.filter(
                DocumentChunk.consultation_id == consultation_id
            )
        
        # Order by document and chunk index
        results = base_query.order_by(
            DocumentChunk.document_id,
            DocumentChunk.chunk_index
        ).limit(limit).all()
        
        # Convert to dictionaries
        context = []
        for chunk in results:
            context.append(chunk.to_dict())
        
        return context
    
    def verify_patient_access(
        self,
        chunk_id: str,
        patient_id: str,
        db: Session
    ) -> bool:
        """
        Verify that a chunk belongs to the specified patient.
        
        Args:
            chunk_id: ID of the chunk
            patient_id: Patient ID to verify against
            db: Database session
            
        Returns:
            True if chunk belongs to patient, False otherwise
        """
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.id == chunk_id
        ).first()
        
        if not chunk:
            return False
        
        return str(chunk.patient_id) == patient_id


# Singleton instance
rag_service = RAGService()
