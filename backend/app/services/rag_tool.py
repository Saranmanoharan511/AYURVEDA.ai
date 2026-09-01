"""
RAG Tool Service

Connects pgvector retrieval for patient-scoped document chunks.
This tool provides semantic search capabilities with strict patient authorization.
"""

import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.rag_service import RAGService
from app.schemas.ai import RAGToolRequest, RAGToolResponse


class RAGTool:
    """
    RAG Tool for patient-aware semantic document retrieval.
    
    This tool wraps the RAG service and provides a clean interface
    for the AI orchestrator to retrieve relevant document chunks.
    
    CRITICAL: All retrievals enforce WHERE patient_id = authorized_patient_id
    to prevent cross-patient data leakage.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService()
    
    def retrieve(self, request: RAGToolRequest) -> RAGToolResponse:
        """
        Retrieve semantically relevant document chunks for a patient.
        
        Args:
            request: RAGToolRequest with query, patient_id, and filters
            
        Returns:
            RAGToolResponse with retrieved chunks and metadata
        """
        start_time = time.time()
        
        try:
            # Use the existing RAG service for retrieval
            result = self.rag_service.retrieve_relevant_chunks(
                query=request.query,
                patient_id=request.patient_id,
                db=self.db,
                consultation_id=request.consultation_id,
                document_type=request.document_type,
                top_k=request.top_k,
                min_similarity=request.min_similarity
            )
            
            retrieval_time = (time.time() - start_time) * 1000
            
            # Format chunks for AI consumption
            formatted_chunks = []
            for chunk_result in result.results:
                formatted_chunks.append({
                    "chunk_id": str(chunk_result.chunk_id),
                    "chunk_text": chunk_result.chunk_text,
                    "similarity": chunk_result.similarity_score,
                    "document_type": chunk_result.document_type,
                    "source_filename": chunk_result.source_filename,
                    "consultation_id": str(chunk_result.consultation_id) if chunk_result.consultation_id else None,
                    "metadata": chunk_result.metadata
                })
            
            return RAGToolResponse(
                query=request.query,
                chunks=formatted_chunks,
                chunk_count=len(formatted_chunks),
                retrieval_time_ms=retrieval_time
            )
            
        except Exception as e:
            retrieval_time = (time.time() - start_time) * 1000
            raise Exception(f"RAG Tool retrieval failed: {str(e)}")
    
    def retrieve_by_client_id(self, client_id: str, query: str, top_k: int = 5) -> RAGToolResponse:
        """
        Retrieve chunks using public client ID instead of internal patient ID.
        
        Args:
            client_id: Public client ID (e.g., AYU-000001)
            query: Search query
            top_k: Number of results to retrieve
            
        Returns:
            RAGToolResponse with retrieved chunks
        """
        # Convert client_id to patient_id using SQL Tool
        from app.services.sql_tool import SQLTool
        sql_tool = SQLTool(self.db)
        
        patient_info = sql_tool.get_patient_by_client_id(client_id)
        if not patient_info:
            raise ValueError(f"Patient not found with client_id: {client_id}")
        
        # Create RAG request
        request = RAGToolRequest(
            query=query,
            patient_id=patient_info['patient_id'],
            top_k=top_k
        )
        
        return self.retrieve(request)
    
    def format_chunks_for_ai(self, response: RAGToolResponse) -> str:
        """
        Format retrieved chunks as a readable string for AI consumption.
        
        Args:
            response: RAGToolResponse
            
        Returns:
            Formatted chunks string
        """
        if not response.chunks:
            return "No relevant document chunks found."
        
        lines = [f"Found {response.chunk_count} relevant document chunks:\n"]
        
        for i, chunk in enumerate(response.chunks, 1):
            lines.append(f"Chunk {i} (Similarity: {chunk['similarity']:.2f}):")
            lines.append(f"  Source: {chunk['source_filename']} ({chunk['document_type']})")
            lines.append(f"  Content: {chunk['chunk_text'][:500]}...")
            if chunk['consultation_id']:
                lines.append(f"  Consultation: {chunk['consultation_id']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_patient_document_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Get a summary of available documents for a patient.
        
        Args:
            patient_id: Patient internal ID
            
        Returns:
            Dictionary with document summary
        """
        from app.models.document_chunk import DocumentChunk
        from sqlalchemy import select, func
        
        query = select(
            DocumentChunk.document_type,
            func.count(DocumentChunk.id).label('chunk_count')
        ).where(
            DocumentChunk.patient_id == patient_id
        ).group_by(
            DocumentChunk.document_type
        )
        
        results = self.db.execute(query).all()
        
        summary = {
            "total_chunks": sum(row.chunk_count for row in results),
            "by_document_type": [
                {
                    "document_type": row.document_type,
                    "chunk_count": row.chunk_count
                }
                for row in results
            ]
        }
        
        return summary
