from arq.connections import RedisSettings

from app.config import settings
from app.workers.tasks import grade_submission, compute_plagiarism   # ← оба импорта


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


class WorkerSettings:
    redis_settings = redis_settings()
    functions = [grade_submission, compute_plagiarism]
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600