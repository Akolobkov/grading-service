from functools import lru_cache

from app.config import settings
from app.ml.analyzer import CodeQualityAnalyzer

@lru_cache(maxsize=1)
def _get_analyzer() -> CodeQualityAnalyzer:
    """Ленивая инициализация: модель грузится один раз на процесс."""
    return CodeQualityAnalyzer(
        model_path=settings.ml_model_path,
        scaler_path=settings.ml_scaler_path,
    )


def predict(code: str) -> tuple[int, dict]:
    """Возвращает (score, metrics)."""
    return _get_analyzer().predict_quality(code)