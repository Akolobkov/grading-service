import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.ngrams import build_ngrams
from app.ml.plagiarism import js_divergence
from app.models import PlagiarismPair, Submission

logger = logging.getLogger(__name__)


async def compute_plagiarism_for_submission(
    db: AsyncSession,
    submission: Submission,
    ngram_size: int = 3,
) -> int:
    """
    Сравнивает сабмит со всеми кандидатами и записывает результаты
    в plagiarism_pairs. Возвращает количество сравнений.
    """
    if submission.tokens is None:
        logger.warning(
            "Submission %s has no tokens, skipping plagiarism",
            submission.id,
        )
        return 0

    candidates = await _find_candidates(db, submission)

    ngrams_a = build_ngrams(submission.tokens, n=ngram_size)

    written = 0
    for candidate in candidates:
        ngrams_b = build_ngrams(candidate.tokens, n=ngram_size)
        jsd = js_divergence(ngrams_a, ngrams_b)

        pair = PlagiarismPair(
            submission_a_id=min(submission.id, candidate.id),
            submission_b_id=max(submission.id, candidate.id),
            metric="jsd",
            value=jsd,
            ngram_size=ngram_size,
        )
        db.add(pair)
        written += 1

    await db.commit()
    logger.info(
        "Plagiarism computed for submission %s: %d pairs",
        submission.id, written,
    )
    return written


async def _find_candidates(
    db: AsyncSession,
    submission: Submission,
) -> list[Submission]:
    """Находит сабмиты-кандидаты для сравнения: то же задание, другой студент, оценённые."""
    stmt = select(Submission).where(
        Submission.task_external_id == submission.task_external_id,
        Submission.student_external_id != submission.student_external_id,
        Submission.status == "graded",
        Submission.tokens.isnot(None),
        Submission.id != submission.id,
    )
    return list((await db.execute(stmt)).scalars().all())