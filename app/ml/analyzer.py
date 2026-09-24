from pathlib import Path

import joblib
import pandas as pd

from app.ml.features import FEATURE_ORDER
from app.ml.parser import CParser


class CodeQualityAnalyzer:
    def __init__(self, model_path: str | Path, scaler_path: str | Path):
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)

    def predict_quality(self, code: str) -> tuple[int, dict]:
        """
        Возвращает (score, metrics).
        score — целое от 1 до 10.
        metrics — сырые метрики парсера (для feedback).
        """
        parser = CParser(code)
        metrics = parser.extract_metrics()

        # Явный порядок колонок — критично для scaler и модели
        df = pd.DataFrame([metrics])[FEATURE_ORDER]

        scaled = self.scaler.transform(df)
        prediction = self.model.predict(scaled)[0]
        score = max(1, min(10, round(float(prediction))))

        return score, metrics