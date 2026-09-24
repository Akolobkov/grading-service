from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Submission
from app.services import ml_adapter, parser_adapter


async def grade(db: AsyncSession, submission: Submission) -> None:
    """Оркестрация оценки: парсинг → ML → сохранение результата."""
    # Метрики для feedback (модель внутри тоже вызовет парсер — это её право)
    metrics = parser_adapter.parse(submission.code)

    # ML ставит оценку в шкале 1..10
    raw_score, _ = ml_adapter.predict(submission.code)

    # Приводим к шкале задания
    if submission.max_score == 10:
        submission.score = float(raw_score)
    else:
        submission.score = round(raw_score / 10 * submission.max_score, 2)

    submission.feedback = metrics
    submission.parser_version = settings.parser_version
    submission.model_version = settings.model_version
    submission.status = "graded"
    submission.graded_at = datetime.now(timezone.utc)
    await db.commit()