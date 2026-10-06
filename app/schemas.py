from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SubmissionStatus = Literal["pending", "grading", "graded", "error"]


class SubmissionCreate(BaseModel):
    student_external_id: str = Field(..., max_length=64)
    task_external_id: str = Field(..., max_length=64)
    group_external_id: str | None = Field(None, max_length=64)
    language: Literal["cpp"] = "cpp"
    code: str = Field(..., min_length=1)
    max_score: float = Field(10.0, gt=0)


class SubmissionAccepted(BaseModel):
    submission_id: int
    status: SubmissionStatus


class SubmissionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_external_id: str
    task_external_id: str
    group_external_id: str | None
    language: str
    status: SubmissionStatus
    score: float | None
    max_score: float
    feedback: dict | None
    error_message: str | None
    parser_version: str | None
    model_version: str | None
    attempt_number: int
    submitted_at: datetime
    graded_at: datetime | None

class PlagiarismMatch(BaseModel):
    submission_id: int
    student_external_id: str
    task_external_id: str
    submitted_at: datetime
    jsd: float
    ngram_size: int


class PlagiarismReport(BaseModel):
    submission_id: int
    metric: str
    count: int
    matches: list[PlagiarismMatch]