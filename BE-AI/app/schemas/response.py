from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    run_id: str
    status: JobStatusEnum
    created_at: datetime
    completed_at: Optional[datetime] = None
    requirement_preview: str
    result: Optional[dict] = None
    error: Optional[str] = None


class JobSummary(BaseModel):
    run_id: str
    status: JobStatusEnum
    created_at: datetime
    completed_at: Optional[datetime] = None
    requirement_preview: str


class AgentV1Response(BaseModel):
    result_text: str
