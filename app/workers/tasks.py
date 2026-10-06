import logging
from datetime import datetime, timezone
from app.database import SessionFactory
from app.models import Submission
from app.services.grading import grade
from app.services.plagiatarizm import compute_plagiarism_for_submission
logger = logging.getLogger(__name__)

async def grade_submission(ctx: dict, submission_id: int) -> dict:
    async with SessionFactory() as db:
        submission = await db.get(Submission, submission_id)
        if submission is None:
            return {"submission_id": submission_id, "status": "not_found"}

        if submission.status != "pending":
            return {"submission_id": submission_id, "status": submission.status}

        submission.status = "grading"
        await db.commit()

        try:
            await grade(db, submission)

            # После успешной оценки — поставить задачу сравнения
            await ctx["redis"].enqueue_job("compute_plagiarism", submission.id)

            return {
                "submission_id": submission_id,
                "status": "graded",
                "score": submission.score,
            }
        except Exception as exc:
            logger.exception("Grading failed for submission %s", submission_id)
            submission.status = "error"
            submission.error_message = str(exc)[:2000]
            submission.graded_at = datetime.now(timezone.utc)
            await db.commit()
            return {"submission_id": submission_id, "status": "error", "error": str(exc)}

async def compute_plagiarism(ctx: dict, submission_id: int) -> dict:
    """ARQ-задача: запускает сравнение сабмита на плагиат."""
    async with SessionFactory() as db:
        submission = await db.get(Submission, submission_id)
        if submission is None:
            return {"submission_id": submission_id, "status": "not_found"}

        try:
            compared = await compute_plagiarism_for_submission(db, submission)
            return {
                "submission_id": submission_id,
                "status": "ok",
                "compared": compared,
            }
        except Exception as exc:
            logger.exception(
                "Plagiarism computation failed for submission %s",
                submission_id,
            )
            return {
                "submission_id": submission_id,
                "status": "error",
                "error": str(exc),
            }