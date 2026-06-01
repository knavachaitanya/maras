from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    OPENAI_API_KEY: str = ""

    PORT: int = 8000
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    MAX_SCRAPE_WORKERS: int = 5
    SCRAPE_TIMEOUT_SECONDS: int = 3
    RESULT_CACHE_TTL_MINUTES: int = 60
    MAX_RESULTS_PER_ENGINE: int = 3

    # Load .env from project root
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        extra="ignore"
    )


settings = Settings()
