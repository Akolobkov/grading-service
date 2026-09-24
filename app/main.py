from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)

    # Создаём пул соединений с Redis
    app.state.arq_redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))

    yield

    # Закрываем пул при остановке
    await app.state.arq_redis.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Grading Service",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()