from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()