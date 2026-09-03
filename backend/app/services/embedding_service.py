"""
Embedding Service

Service for generating vector embeddings from text using configurable embedding providers.
This service supports multiple embedding providers including OpenAI, Amazon Bedrock,
and local models for development.

Note: This is AWS Code-Only Mode. The service code is written but actual
embedding provider resources will be configured manually after Sprint 8.
"""

import os
import logging
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings from text."""
    
    def __init__(self):
        self.embedding_provider = settings.EMBEDDING_PROVIDER or "bedrock"
        self.embedding_model = settings.EMBEDDING_MODEL or "amazon.titan-embed-text-v2:0"
        self.embedding_dimensions = settings.EMBEDDING_DIMENSIONS or 1024
        
        logger.info(f"Initializing EmbeddingService with provider: {self.embedding_provider}, model: {self.embedding_model}, dimensions: {self.embedding_dimensions}")
        
        # Initialize provider-specific clients
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the embedding provider client."""
        if self.embedding_provider == "openai":
            try:
                import openai
                if settings.OPENAI_API_KEY:
                    self.openai_client = openai.OpenAI(
                        api_key=settings.OPENAI_API_KEY
                    )
                    logger.info("OpenAI embedding client initialized successfully")
                else:
                    logger.warning("OpenAI API key not configured. Embedding service will be disabled.")
                    self.openai_client = None
            except ImportError:
                logger.error("OpenAI package not installed. Install with: pip install openai")
                self.openai_client = None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.openai_client = None
        elif self.embedding_provider == "bedrock":
            try:
                import boto3
                self.bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=settings.AWS_REGION
                )
                logger.info(f"Bedrock embedding client initialized successfully in region {settings.AWS_REGION}")
            except ImportError:
                logger.error("Boto3 package not installed. Install with: pip install boto3")
                self.bedrock_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock client: {str(e)}")
                self.bedrock_client = None
        elif self.embedding_provider == "local":
            # For local development with sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
                self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding_dimensions = 384
                logger.info("Local sentence-transformers model initialized successfully")
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                self.local_model = None
            except Exception as e:
                logger.error(f"Failed to initialize local model: {str(e)}")
                self.local_model = None
    
    def generate_embedding(
        self,
        text: str
    ) -> Optional[List[float]]:
        """
        Generate a vector embedding for the given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Vector embedding as a list of floats, None if generation fails
            
        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        text_length = len(text)
        logger.debug(f"Generating embedding for text of length {text_length} using provider {self.embedding_provider}")
        
        try:
            if self.embedding_provider == "openai":
                return self._generate_openai_embedding(text)
            elif self.embedding_provider == "bedrock":
                return self._generate_bedrock_embedding(text)
            elif self.embedding_provider == "local":
                return self._generate_local_embedding(text)
            else:
                logger.error(f"Unsupported embedding provider: {self.embedding_provider}")
                raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            raise ValueError("OpenAI client not initialized")
        
        logger.debug(f"Generating OpenAI embedding using model {self.embedding_model}")
        
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Successfully generated OpenAI embedding with dimensions {len(embedding)}")
        
        return embedding
    
    def _generate_bedrock_embedding(self, text: str) -> List[float]:
        """Generate embedding using Amazon Bedrock."""
        if not self.bedrock_client:
            logger.error("Bedrock client not initialized")
            raise ValueError("Bedrock client not initialized")
        
        import json
        
        # Use Amazon Titan Embeddings model
        model_id = self.embedding_model or "amazon.titan-embed-text-v2:0"
        
        logger.debug(f"Generating Bedrock embedding using model {model_id}")
        
        # Titan V2 uses different request format
        if "v2" in model_id.lower():
            body = {
                "inputText": text,
                "dimensions": self.embedding_dimensions,
                "normalize": True
            }
        else:
            # Titan V1 format
            body = {
                "inputText": text
            }
        
        response = self.bedrock_client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response.get('body').read())
        
        # Titan V2 uses different response format
        if "v2" in model_id.lower():
            embedding = response_body.get('embedding')
        else:
            embedding = response_body.get('embedding')
        
        if embedding:
            logger.debug(f"Successfully generated Bedrock embedding with dimensions {len(embedding)}")
        else:
            logger.error("Bedrock response did not contain embedding")
        
        return embedding
    
    def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local sentence-transformers model."""
        if not self.local_model:
            logger.error("Local model not initialized")
            raise ValueError("Local model not initialized")
        
        logger.debug("Generating local embedding using sentence-transformers")
        
        embedding = self.local_model.encode(text)
        embedding_list = embedding.tolist()
        
        logger.debug(f"Successfully generated local embedding with dimensions {len(embedding_list)}")
        
        return embedding_list
    
    def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of vector embeddings (or None for failed generations)
        """
        logger.info(f"Generating batch embeddings for {len(texts)} texts")
        embeddings = []
        successful_count = 0
        failed_count = 0
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                if embedding:
                    successful_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to generate embedding for text index {i}")
            except Exception as e:
                logger.error(f"Failed to generate embedding for text index {i}: {str(e)}")
                embeddings.append(None)
                failed_count += 1
        
        logger.info(f"Batch embedding generation complete: {successful_count} successful, {failed_count} failed")
        
        return embeddings
    
    def get_embedding_dimensions(self) -> int:
        """
        Get the dimensions of the embedding vectors.
        
        Returns:
            Number of dimensions in the embedding vectors
        """
        return self.embedding_dimensions


# Singleton instance
embedding_service = EmbeddingService()
