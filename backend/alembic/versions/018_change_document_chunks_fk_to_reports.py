"""
change document_chunks foreign key to reports.id for reports-only RAG architecture

Revision ID: 018_reports_only_fk
Revises: 017_vector_dims
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_reports_only_fk'
down_revision = '017_vector_dims'
branch_labels = None
depends_on = None


def upgrade():
    """
    Change document_chunks.document_id foreign key from patient_documents.id to reports.id
    This aligns with the requirement that only reports undergo AI/RAG processing.
    """
    
    # Drop existing foreign key constraint to patient_documents
    try:
        op.drop_constraint('document_chunks_document_id_fkey', 'document_chunks', type_='foreignkey')
        print("Dropped existing FK constraint to patient_documents")
    except Exception as e:
        print(f"Could not drop FK constraint (may not exist): {str(e)}")
    
    # Add new foreign key constraint to reports
    try:
        op.create_foreign_key(
            'document_chunks_document_id_fkey',
            'document_chunks', 'reports',
            ['document_id'], ['id'],
            ondelete='CASCADE'
        )
        print("Added new FK constraint to reports")
    except Exception as e:
        print(f"Could not add FK constraint to reports: {str(e)}")
        raise


def downgrade():
    """
    Revert back to original foreign key constraint to patient_documents
    """
    
    # Drop foreign key constraint to reports
    try:
        op.drop_constraint('document_chunks_document_id_fkey', 'document_chunks', type_='foreignkey')
        print("Dropped FK constraint to reports")
    except Exception as e:
        print(f"Could not drop FK constraint: {str(e)}")
    
    # Restore original foreign key constraint to patient_documents
    try:
        op.create_foreign_key(
            'document_chunks_document_id_fkey',
            'document_chunks', 'patient_documents',
            ['document_id'], ['id'],
            ondelete='CASCADE'
        )
        print("Restored FK constraint to patient_documents")
    except Exception as e:
        print(f"Could not restore FK constraint to patient_documents: {str(e)}")
        raise
