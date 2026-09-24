from arq.connections import RedisSettings

from app.config import settings


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


class WorkerSettings:
    redis_settings = redis_settings()
    functions: list = []      # задачи добавим на шаге 4
    max_jobs = 10
    job_timeout = 300