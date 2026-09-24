from app.config import settings
from app.ml.parser import CParser

PARSER_VERSION = settings.parser_version


def parse(code: str) -> dict:
    """Возвращает метрики парсера для feedback и отладки."""
    return CParser(code).extract_metrics()