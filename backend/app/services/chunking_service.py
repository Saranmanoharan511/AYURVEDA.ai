"""
Chunking Service

Service for splitting documents into manageable chunks for embedding generation
and RAG retrieval. This service implements various chunking strategies including
fixed-size chunking, semantic chunking, and paragraph-based chunking.
"""

import logging
from typing import List, Dict, Any, Optional
from app.schemas.document_processing import ChunkingConfig

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks."""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks based on the configured strategy.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunks with text, index, and metadata
        """
        if not text or not text.strip():
            return []
        
        logger.info(f"Starting chunking for text of length {len(text)} characters")
        
        # Normalize text
        text = self._normalize_text(text)
        logger.debug(f"Text normalized to {len(text)} characters")
        
        # Choose chunking strategy based on text characteristics
        if self._should_use_paragraph_chunking(text):
            logger.debug("Using paragraph-based chunking strategy")
            chunks = self._chunk_by_paragraphs(text)
        else:
            logger.debug("Using fixed-size chunking strategy")
            chunks = self._chunk_by_size(text)
        
        # Limit maximum chunks to prevent memory issues
        if len(chunks) > self.config.max_chunks:
            logger.warning(f"Reducing chunks from {len(chunks)} to {self.config.max_chunks} to prevent memory issues")
            chunks = chunks[:self.config.max_chunks]
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Attach metadata to chunks (optimized to reduce memory)
        if metadata:
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_strategy': 'paragraph' if self._should_use_paragraph_chunking(text) else 'fixed_size'
                }
                chunk['metadata'] = chunk_metadata
        else:
            for i, chunk in enumerate(chunks):
                chunk['metadata'] = {
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_strategy': 'paragraph' if self._should_use_paragraph_chunking(text) else 'fixed_size'
                }
        
        return chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing excessive whitespace."""
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        # Preserve newlines if configured
        if self.config.preserve_newlines:
            # Ensure single newlines between paragraphs
            text = '\n\n'.join([p.strip() for p in text.split('\n\n') if p.strip()])
        
        return text
    
    def _should_use_paragraph_chunking(self, text: str) -> bool:
        """Determine if paragraph-based chunking should be used."""
        # Use paragraph chunking if text has clear paragraph structure
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        # Use paragraph chunking if:
        # - There are multiple paragraphs
        # - Average paragraph length is reasonable
        if len(paragraphs) > 1:
            avg_length = sum(len(p) for p in paragraphs) / len(paragraphs)
            return self.config.chunk_size * 0.5 < avg_length < self.config.chunk_size * 2
        
        return False
    
    def _chunk_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, start new chunk
            if len(current_chunk) + len(paragraph) > self.config.chunk_size and current_chunk:
                chunks.append({
                    'chunk_index': chunk_index,
                    'chunk_text': current_chunk.strip()
                })
                chunk_index += 1
                current_chunk = paragraph
                
                # Stop if we've reached max chunks
                if len(chunks) >= self.config.max_chunks:
                    break
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add remaining content if within limits
        if current_chunk and len(current_chunk) >= self.config.min_chunk_size and len(chunks) < self.config.max_chunks:
            chunks.append({
                'chunk_index': chunk_index,
                'chunk_text': current_chunk.strip()
            })
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text by fixed size with overlap."""
        chunks = []
        chunk_index = 0
        start = 0
        text_length = len(text)
        
        while start < text_length and len(chunks) < self.config.max_chunks:
            # Calculate end position
            end = start + self.config.chunk_size
            
            # If this is the last chunk, take remaining text
            if end >= text_length:
                end = text_length
            else:
                # Try to break at a word boundary
                while end > start and text[end] not in ' \n\t':
                    end -= 1
                
                # If no word boundary found, force break
                if end == start:
                    end = start + self.config.chunk_size
            
            chunk_text = text[start:end].strip()
            
            # Only add if it meets minimum size
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append({
                    'chunk_index': chunk_index,
                    'chunk_text': chunk_text
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.config.chunk_overlap
        
        return chunks
    
    def chunk_with_context(
        self,
        text: str,
        context_size: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Chunk text with surrounding context for each chunk.
        
        Args:
            text: Text to chunk
            context_size: Number of characters to include as context
            
        Returns:
            List of chunks with context
        """
        base_chunks = self.chunk_text(text)
        
        for i, chunk in enumerate(base_chunks):
            context_before = ""
            context_after = ""
            
            # Get context from previous chunks
            if i > 0:
                prev_chunk = base_chunks[i - 1]['chunk_text']
                context_before = prev_chunk[-context_size:] if len(prev_chunk) > context_size else prev_chunk
            
            # Get context from next chunks
            if i < len(base_chunks) - 1:
                next_chunk = base_chunks[i + 1]['chunk_text']
                context_after = next_chunk[:context_size] if len(next_chunk) > context_size else next_chunk
            
            # Add context to chunk
            chunk['context_before'] = context_before
            chunk['context_after'] = context_after
            chunk['full_text_with_context'] = f"{context_before} {chunk['chunk_text']} {context_after}".strip()
        
        return base_chunks


# Singleton instance
chunking_service = ChunkingService()
