"""
Async ORM Models (Parallel Infrastructure)
==========================================
Four core models built on AsyncBase.  This file does NOT import or touch
the existing db_models.py / database.py in any way.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from async_database import AsyncBase


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class UserRole(str, enum.Enum):
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    ADMIN = "ADMIN"


class PolicyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ──────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────

class User(AsyncBase):
    """Platform user with role-based access control."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum", create_constraint=True),
        nullable=False,
        default=UserRole.MAKER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
    )

    # Relationships
    policies_created: Mapped[list["CreditPolicy"]] = relationship(
        back_populates="creator", lazy="selectin",
    )
    requests_made: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="requester",
        foreign_keys="[ApprovalRequest.requested_by]",
        lazy="selectin",
    )
    requests_approved: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="approver",
        foreign_keys="[ApprovalRequest.approved_by]",
        lazy="selectin",
    )
    audit_entries: Mapped[list["AuditLog"]] = relationship(
        back_populates="user", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role.value}]>"


class CreditPolicy(AsyncBase):
    """Versioned credit‑decision rule‑set stored as JSONB."""
    __tablename__ = "credit_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[PolicyStatus] = mapped_column(
        SAEnum(PolicyStatus, name="policy_status_enum", create_constraint=True),
        nullable=False,
        default=PolicyStatus.DRAFT,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    creator: Mapped["User"] = relationship(back_populates="policies_created")
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="policy", lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_policy_name_version"),
    )

    def __repr__(self) -> str:
        return f"<CreditPolicy {self.name} v{self.version} [{self.status.value}]>"


class ApprovalRequest(AsyncBase):
    """Maker‑Checker approval workflow record."""
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("credit_policies.id"), nullable=False,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approval_status_enum", create_constraint=True),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
    )

    # Relationships
    policy: Mapped["CreditPolicy"] = relationship(back_populates="approval_requests")
    requester: Mapped["User"] = relationship(
        back_populates="requests_made",
        foreign_keys=[requested_by],
    )
    approver: Mapped["User"] = relationship(
        back_populates="requests_approved",
        foreign_keys=[approved_by],
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest {self.id} [{self.status.value}]>"


class AuditLog(AsyncBase):
    """Immutable, append‑only audit trail for regulatory compliance."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_uuid,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="audit_entries")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.entity_type}/{self.entity_id}>"


class AnalysisSession(AsyncBase):
    """Stores the state of a document extraction and risk analysis session."""
    __tablename__ = "analysis_sessions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(64), default="INITIATED")
    raw_extracts: Mapped[dict] = mapped_column(JSON, default=dict)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class WorkflowDefinition(AsyncBase):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="Untitled Workflow")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    definition_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    nodes: Mapped[list["WorkflowNodeDefinition"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    edges: Mapped[list["WorkflowEdgeDefinition"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNodeDefinition(AsyncBase):
    __tablename__ = "workflow_node_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[str] = mapped_column(String(128), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True)
    node_id: Mapped[str] = mapped_column(String(128))
    node_type: Mapped[str] = mapped_column(String(64))
    label: Mapped[str | None] = mapped_column(String(255))
    position_x: Mapped[float] = mapped_column(Float, default=0)
    position_y: Mapped[float] = mapped_column(Float, default=0)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    execution_config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    workflow: Mapped["WorkflowDefinition"] = relationship(back_populates="nodes")


class WorkflowEdgeDefinition(AsyncBase):
    __tablename__ = "workflow_edge_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[str] = mapped_column(String(128), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), index=True)
    edge_id: Mapped[str] = mapped_column(String(128))
    source_node_id: Mapped[str] = mapped_column(String(128))
    target_node_id: Mapped[str] = mapped_column(String(128))
    source_handle: Mapped[str | None] = mapped_column(String(64))
    target_handle: Mapped[str | None] = mapped_column(String(64))
    edge_type: Mapped[str | None] = mapped_column(String(64))
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    workflow: Mapped["WorkflowDefinition"] = relationship(back_populates="edges")


class ExecutionRun(AsyncBase):
    __tablename__ = "execution_runs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128), ForeignKey("workflow_definitions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    initial_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    final_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    workflow: Mapped["WorkflowDefinition | None"] = relationship()


class NodeExecutionLog(AsyncBase):
    __tablename__ = "node_execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(128), ForeignKey("execution_runs.id", ondelete="CASCADE"), index=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128))
    node_id: Mapped[str] = mapped_column(String(128))
    node_type: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    input_payload_json: Mapped[dict | None] = mapped_column(JSON)
    output_payload_json: Mapped[dict | None] = mapped_column(JSON)
    source_edges_json: Mapped[list | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class DeadLetterExecution(AsyncBase):
    __tablename__ = "dead_letter_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(128), ForeignKey("execution_runs.id", ondelete="CASCADE"), unique=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128))
    failure_stage: Mapped[str] = mapped_column(String(64), default="workflow")
    reason: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
