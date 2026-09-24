from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://grading:grading@localhost:5432/grading"
    redis_url: str = "redis://localhost:6379/0"

    max_code_size_bytes: int = 512 * 1024
    model_version: str = "v0.0.0-stub"
    parser_version: str = "v0.0.0-stub"

    service_token: str = "change-me-in-production"

    ml_dir: Path = Path(__file__).resolve().parent / "ml"
    ml_model_filename: str = "code_quality_model.pkl"
    ml_scaler_filename: str = "scaler.pkl"
    parser_version: str = "1.0.0"
    model_version: str = "v1.0.0"

    @property
    def ml_model_path(self) -> Path:
        return self.ml_dir / self.ml_model_filename

    @property
    def ml_scaler_path(self) -> Path:
        return self.ml_dir / self.ml_scaler_filename


settings = Settings()