from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_role = Column(String(50), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_identifier = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    audit_metadata = Column(JSONB(), nullable=True)  # Renamed from metadata
    old_values = Column(JSONB(), nullable=True)
    new_values = Column(JSONB(), nullable=True)
    success = Column(Boolean(), nullable=False, default=True, index=True)
    error_message = Column(Text(), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default="NOW()", nullable=False, index=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "actor_user_id": str(self.actor_user_id) if self.actor_user_id else None,
            "actor_role": self.actor_role,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "resource_identifier": self.resource_identifier,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.audit_metadata,  # Keep 'metadata' in API response
            "old_values": self.old_values,
            "new_values": self.new_values,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type}, actor_role={self.actor_role})>"
