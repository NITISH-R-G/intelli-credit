from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Centralized configuration manager for strictly typing and validating env variables."""
    ENVIRONMENT: str = "production"
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # ML & Core Logic Defaults
    DEFAULT_INDUSTRY_RISK: float = 0.3
    DEFAULT_BUREAU_SCORE: int = 700
    DEFAULT_CREDIT_HISTORY_MONTHS: int = 60
    DEFAULT_PD_SCORE_FALLBACK: float = 0.15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
