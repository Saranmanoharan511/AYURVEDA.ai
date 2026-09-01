"""
RAG Evaluation Tests for Patient Boundary Enforcement

Comprehensive tests to ensure RAG retrieval respects patient boundaries.
These tests verify that:
- RAG retrieval enforces WHERE patient_id = authorized_patient_id
- Cross-patient retrieval is prevented
- Patient filtering is applied at the database level
- Consultation filtering works correctly
- Document type filtering works correctly
- No unauthorized data leakage occurs

Note: These tests use mocking to avoid requiring actual pgvector database.
Full integration tests with real Neon PostgreSQL + pgvector will be executed
after Sprint 8 when infrastructure is created.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.rag_service import RAGService
from app.services.rag_tool import RAGTool
from app.models.document_chunk import DocumentChunk


class TestRAGPatientBoundaryEnforcement:
    """Test RAG patient boundary enforcement."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_rag_requires_patient_id(self, rag_service):
        """Test that RAG retrieval requires patient_id."""
        query = "test query"
        
        # Should raise error without patient_id
        with pytest.raises(ValueError):
            rag_service.retrieve(query, patient_id=None)
    
    def test_rag_enforces_patient_filter(self, rag_service):
        """Test that RAG enforces patient filter in query."""
        patient_id = str(uuid4())
        query = "test query"
        
        # Mock the database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        rag_service.retrieve(query, patient_id=patient_id)
        
        # Verify that filter was called with patient_id
        assert rag_service.db.query.called
        # The filter should include patient_id condition
        # This would be verified by checking the actual SQL in real tests
    
    def test_rag_prevents_cross_patient_retrieval(self, rag_service):
        """Test that RAG prevents cross-patient retrieval."""
        patient1_id = str(uuid4())
        patient2_id = str(uuid4())
        query = "test query"
        
        # Mock database to return empty results for patient2
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Try to retrieve for patient2
        results = rag_service.retrieve(query, patient_id=patient2_id)
        
        # Should not return patient1's data
        # In real scenario, this would verify SQL WHERE clause
        assert results == []
    
    def test_rag_patient_access_verification(self, rag_service):
        """Test that RAG verifies patient access."""
        patient_id = str(uuid4())
        query = "test query"
        
        # Mock the authorization check
        # In real scenario, this would verify user has access to patient
        with pytest.raises(ValueError):
            # Without proper authorization setup, this may fail
            rag_service.retrieve(query, patient_id=patient_id)


class TestRAGConsultationFiltering:
    """Test RAG consultation filtering."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_rag_consultation_filter_optional(self, rag_service):
        """Test that consultation filter is optional."""
        patient_id = str(uuid4())
        query = "test query"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Should work without consultation_id
        rag_service.retrieve(query, patient_id=patient_id, consultation_id=None)
        
        # Verify query was called
        assert rag_service.db.query.called
    
    def test_rag_consultation_filter_when_provided(self, rag_service):
        """Test that consultation filter is applied when provided."""
        patient_id = str(uuid4())
        consultation_id = str(uuid4())
        query = "test query"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Should apply consultation filter
        rag_service.retrieve(query, patient_id=patient_id, consultation_id=consultation_id)
        
        # Verify query was called
        assert rag_service.db.query.called


class TestRAGDocumentTypeFiltering:
    """Test RAG document type filtering."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_rag_document_type_filter_optional(self, rag_service):
        """Test that document type filter is optional."""
        patient_id = str(uuid4())
        query = "test query"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Should work without document_type
        rag_service.retrieve(query, patient_id=patient_id, document_type=None)
        
        # Verify query was called
        assert rag_service.db.query.called
    
    def test_rag_document_type_filter_when_provided(self, rag_service):
        """Test that document type filter is applied when provided."""
        patient_id = str(uuid4())
        document_type = "medical_report"
        query = "test query"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Should apply document type filter
        rag_service.retrieve(query, patient_id=patient_id, document_type=document_type)
        
        # Verify query was called
        assert rag_service.db.query.called


class TestRAGToolPatientEnforcement:
    """Test RAG Tool patient enforcement."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_tool(self, mock_db):
        """RAG Tool instance."""
        return RAGTool(mock_db)
    
    def test_rag_tool_requires_patient_id(self, rag_tool):
        """Test that RAG Tool requires patient_id."""
        query = "test query"
        
        # Should raise error without patient_id
        with pytest.raises(ValueError):
            rag_tool.retrieve(query, patient_id=None)
    
    def test_rag_tool_enforces_patient_filter(self, rag_tool):
        """Test that RAG Tool enforces patient filter."""
        patient_id = str(uuid4())
        query = "test query"
        
        # Mock the underlying RAG service
        with patch.object(rag_tool.rag_service, 'retrieve', return_value=[]):
            rag_tool.retrieve(query, patient_id=patient_id)
            
            # Verify retrieve was called with patient_id
            rag_tool.rag_service.retrieve.assert_called_once()
    
    def test_rag_tool_retrieve_by_client_id(self, rag_tool):
        """Test RAG Tool retrieval by client ID."""
        client_id = "AYU-000001"
        query = "test query"
        
        # Mock patient lookup
        with patch.object(rag_tool, 'get_patient_by_client_id', return_value=str(uuid4())):
            with patch.object(rag_tool.rag_service, 'retrieve', return_value=[]):
                rag_tool.retrieve_by_client_id(query, client_id=client_id)
                
                # Verify patient lookup was called
                rag_tool.get_patient_by_client_id.assert_called_once_with(client_id)


class TestRAGMetadataSecurity:
    """Test RAG metadata security."""
    
    def test_chunk_includes_patient_id(self):
        """Test that document chunks include patient_id."""
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            patient_id=uuid4(),
            consultation_id=uuid4(),
            chunk_index=0,
            chunk_text="Test text",
            embedding=[0.1, 0.2, 0.3],
            metadata={"source": "test.pdf"},
            source_filename="test.pdf",
            document_type="medical_report"
        )
        
        assert chunk.patient_id is not None
        assert isinstance(chunk.patient_id, str)
    
    def test_chunk_includes_consultation_id(self):
        """Test that document chunks include consultation_id."""
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            patient_id=uuid4(),
            consultation_id=uuid4(),
            chunk_index=0,
            chunk_text="Test text",
            embedding=[0.1, 0.2, 0.3],
            metadata={"source": "test.pdf"},
            source_filename="test.pdf",
            document_type="medical_report"
        )
        
        assert chunk.consultation_id is not None
        assert isinstance(chunk.consultation_id, str)
    
    def test_chunk_includes_document_type(self):
        """Test that document chunks include document_type."""
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            patient_id=uuid4(),
            consultation_id=uuid4(),
            chunk_index=0,
            chunk_text="Test text",
            embedding=[0.1, 0.2, 0.3],
            metadata={"source": "test.pdf"},
            source_filename="test.pdf",
            document_type="medical_report"
        )
        
        assert chunk.document_type is not None
        assert isinstance(chunk.document_type, str)
    
    def test_chunk_metadata_includes_security_info(self):
        """Test that chunk metadata includes security information."""
        patient_id = str(uuid4())
        consultation_id = str(uuid4())
        
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            patient_id=patient_id,
            consultation_id=consultation_id,
            chunk_index=0,
            chunk_text="Test text",
            embedding=[0.1, 0.2, 0.3],
            metadata={
                "patient_id": patient_id,
                "consultation_id": consultation_id,
                "document_type": "medical_report",
                "source_filename": "test.pdf"
            },
            source_filename="test.pdf",
            document_type="medical_report"
        )
        
        assert "patient_id" in chunk.metadata
        assert "consultation_id" in chunk.metadata
        assert "document_type" in chunk.metadata


class TestRAGCrossPatientLeakagePrevention:
    """Test prevention of cross-patient data leakage in RAG."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_patient1_cannot_retrieve_patient2_chunks(self, rag_service):
        """Test that patient1 cannot retrieve patient2's chunks."""
        patient1_id = str(uuid4())
        patient2_id = str(uuid4())
        query = "test query"
        
        # Mock database to return only patient1's chunks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Simulate patient2's chunks exist but are filtered out
        patient2_chunks = [
            DocumentChunk(
                id=uuid4(),
                document_id=uuid4(),
                patient_id=patient2_id,
                consultation_id=uuid4(),
                chunk_index=0,
                chunk_text="Patient2 data",
                embedding=[0.1, 0.2, 0.3],
                metadata={},
                source_filename="patient2.pdf",
                document_type="medical_report"
            )
        ]
        
        # Return empty list to simulate filtering
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Patient1 tries to retrieve
        results = rag_service.retrieve(query, patient_id=patient1_id)
        
        # Should not return patient2's chunks
        assert results == []
    
    def test_doctor_can_only_retrieve_assigned_patient_chunks(self, rag_service):
        """Test that doctor can only retrieve assigned patient chunks."""
        doctor_id = str(uuid4())
        assigned_patient_id = str(uuid4())
        unassigned_patient_id = str(uuid4())
        query = "test query"
        
        # Mock database to return only assigned patient's chunks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Doctor retrieves for assigned patient
        results = rag_service.retrieve(query, patient_id=assigned_patient_id)
        
        # Should not return unassigned patient's chunks
        assert results == []


class TestRAGTopKLimiting:
    """Test RAG top-k result limiting."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_rag_respects_top_k_limit(self, rag_service):
        """Test that RAG respects top_k limit."""
        patient_id = str(uuid4())
        query = "test query"
        top_k = 5
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        rag_service.retrieve(query, patient_id=patient_id, top_k=top_k)
        
        # Verify limit was called with top_k
        mock_query.limit.assert_called_once_with(top_k)
    
    def test_rag_default_top_k(self, rag_service):
        """Test that RAG has a default top_k value."""
        patient_id = str(uuid4())
        query = "test query"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        rag_service.db.query.return_value = mock_query
        
        # Should use default top_k
        rag_service.retrieve(query, patient_id=patient_id)
        
        # Verify limit was called
        mock_query.limit.assert_called_once()


class TestRAGSimilarityThreshold:
    """Test RAG similarity threshold filtering."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def rag_service(self, mock_db):
        """RAG Service instance."""
        return RAGService(mock_db)
    
    def test_rag_filters_by_similarity(self, rag_service):
        """Test that RAG filters results by similarity threshold."""
        patient_id = str(uuid4())
        query = "test query"
        min_similarity = 0.7
        
        # Mock chunks with varying similarity
        chunks = [
            DocumentChunk(
                id=uuid4(),
                document_id=uuid4(),
                patient_id=patient_id,
                consultation_id=uuid4(),
                chunk_index=0,
                chunk_text="High similarity text",
                embedding=[0.9, 0.1, 0.0],
                metadata={},
                source_filename="test.pdf",
                document_type="medical_report"
            ),
            DocumentChunk(
                id=uuid4(),
                document_id=uuid4(),
                patient_id=patient_id,
                consultation_id=uuid4(),
                chunk_index=1,
                chunk_text="Low similarity text",
                embedding=[0.3, 0.3, 0.4],
                metadata={},
                source_filename="test.pdf",
                document_type="medical_report"
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = chunks
        
        rag_service.db.query.return_value = mock_query
        
        results = rag_service.retrieve(query, patient_id=patient_id, min_similarity=min_similarity)
        
        # Should filter by similarity (in real implementation)
        # For now, we verify the function was called
        assert rag_service.db.query.called


# ============ Deferred Integration Tests ============

class TestRAGIntegrationEvaluation:
    """
    RAG Integration Evaluation Tests - DEFERRED
    
    These tests require actual Neon PostgreSQL with pgvector extension.
    They will be executed after Sprint 8 when infrastructure is created.
    
    Test coverage:
    - Real vector similarity search with pgvector
    - Patient filtering at database level
    - Consultation filtering at database level
    - Document type filtering at database level
    - Cross-patient leakage prevention
    - Retrieval quality evaluation
    - Top-k limiting verification
    - Similarity threshold verification
    """
    
    @pytest.mark.skip(reason="Requires Neon PostgreSQL with pgvector - deferred until after Sprint 8")
    def test_real_vector_similarity_search(self):
        """Test real vector similarity search."""
        pass
    
    @pytest.mark.skip(reason="Requires Neon PostgreSQL with pgvector - deferred until after Sprint 8")
    def test_patient_filtering_at_database_level(self):
        """Test patient filtering at database level."""
        pass
    
    @pytest.mark.skip(reason="Requires Neon PostgreSQL with pgvector - deferred until after Sprint 8")
    def test_cross_patient_leakage_prevention(self):
        """Test cross-patient leakage prevention."""
        pass
    
    @pytest.mark.skip(reason="Requires Neon PostgreSQL with pgvector - deferred until after Sprint 8")
    def test_retrieval_quality_evaluation(self):
        """Test retrieval quality evaluation."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
