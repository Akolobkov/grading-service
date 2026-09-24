import hashlib
from datetime import datetime, timezone
from fastapi import Request

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Submission
from app.schemas import SubmissionAccepted, SubmissionCreate, SubmissionResult

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_submission(
    payload: SubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> SubmissionAccepted:
    # 1. Проверяем размер кода
    code_size_bytes = len(payload.code.encode("utf-8"))
    if code_size_bytes > settings.max_code_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Code size {code_size_bytes} exceeds limit {settings.max_code_size_bytes}",
        )

    # 2. Считаем хэш
    code_hash = hashlib.sha256(payload.code.encode("utf-8")).hexdigest()

    # 3. Определяем номер попытки
    count_stmt = select(func.count()).select_from(Submission).where(
        Submission.student_external_id == payload.student_external_id,
        Submission.task_external_id == payload.task_external_id,
    )
    existing = (await db.execute(count_stmt)).scalar_one()
    attempt_number = existing + 1

    # 4. Создаём запись
    submission = Submission(
        student_external_id=payload.student_external_id,
        task_external_id=payload.task_external_id,
        group_external_id=payload.group_external_id,
        language=payload.language,
        code=payload.code,
        code_hash=code_hash,
        code_size_bytes=code_size_bytes,
        status="pending",
        max_score=payload.max_score,
        attempt_number=attempt_number,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Ставим задачу в очередь через уже созданный пул
    await request.app.state.arq_redis.enqueue_job("grade_submission", submission.id)

    return SubmissionAccepted(
        submission_id=submission.id,
        status=submission.status,
    )


@router.get("/{submission_id}", response_model=SubmissionResult)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_session),
) -> SubmissionResult:
    submission = await db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found",
        )
    return SubmissionResult.model_validate(submission, from_attributes=True)