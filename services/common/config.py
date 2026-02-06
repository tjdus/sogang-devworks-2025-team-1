from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://agent:agent1234@localhost:5432/agent_system"

    # LLM
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"

    # Service URLs
    WORKER_URL: str = "http://localhost:8001"
    EVALUATOR_URL: str = "http://localhost:8002"

    # Optimizer
    OPTIMIZER_FAILURE_THRESHOLD: int = 3
    OPTIMIZER_LOOKBACK_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
