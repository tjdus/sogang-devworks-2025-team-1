import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(64), nullable=False, index=True)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    change_reason = Column(Text, nullable=True)
    created_by = Column(String(64), nullable=False, default="system")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    task_type = Column(String(64), nullable=False, index=True)
    user_input = Column(Text, nullable=False)
    refined_input = Column(Text, nullable=True)
    prompt_version = Column(Integer, nullable=True)
    worker_output = Column(Text, nullable=True)
    worker_latency_ms = Column(Integer, nullable=True)
    evaluation_score = Column(Float, nullable=True)
    evaluation_passed = Column(Boolean, nullable=True)
    evaluation_detail = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class OptimizationReport(Base):
    __tablename__ = "optimization_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(64), nullable=False)
    before_prompt_version = Column(Integer, nullable=False)
    before_prompt_content = Column(Text, nullable=False)
    after_prompt_version = Column(Integer, nullable=False)
    after_prompt_content = Column(Text, nullable=False)
    failure_analysis = Column(JSON, nullable=True)
    improvement_pct = Column(Float, nullable=True)
    triggered_by = Column(String(64), nullable=False, default="cronjob")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
