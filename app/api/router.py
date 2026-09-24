from fastapi import APIRouter

from app.api import health, submissions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(submissions.router)