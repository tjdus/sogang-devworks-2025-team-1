from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Manager ---
class RequestInput(BaseModel):
    user_input: str = Field(..., min_length=1, description="User's raw request")
    task_type: str = Field(default="code_generation", description="Task type")


class RequestResponse(BaseModel):
    request_id: UUID
    refined_input: str
    worker_output: str
    evaluation_score: float
    evaluation_passed: bool
    prompt_version: int


# --- Worker ---
class TaskInput(BaseModel):
    request_id: UUID
    task_type: str = "code_generation"
    refined_input: str


class TaskOutput(BaseModel):
    request_id: UUID
    output: str
    prompt_version: int
    latency_ms: int


# --- Evaluator ---
class EvaluateInput(BaseModel):
    request_id: UUID
    task_type: str = "code_generation"
    user_input: str
    refined_input: str
    worker_output: str


class EvaluationDetail(BaseModel):
    rule_score: float = Field(ge=0, le=1)
    llm_score: float = Field(ge=0, le=1)
    rule_details: dict = {}
    llm_details: dict = {}


class EvaluateOutput(BaseModel):
    request_id: UUID
    score: float
    passed: bool
    detail: EvaluationDetail


# --- Optimizer ---
class OptimizationResult(BaseModel):
    task_type: str
    before_version: int
    after_version: int
    failure_count: int
    improvement_summary: str


# --- Prompt ---
class PromptInfo(BaseModel):
    id: int
    task_type: str
    content: str
    version: int
    is_active: bool
    created_by: str
    created_at: datetime


# --- Health ---
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str = "1.0.0"
