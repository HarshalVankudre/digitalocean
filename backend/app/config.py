from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "gradient-backend"
    APP_DEBUG: bool = False
    API_CORS_ORIGINS: str = "http://localhost:5173"

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    MONGODB_URI: str
    MONGODB_DB: str = "gradient_app"

    DO_AGENT_BASE_URL: str | None = None
    DO_AGENT_ACCESS_KEY: str | None = None

    DO_INCLUDE_RETRIEVAL_INFO: bool = True
    DO_INCLUDE_FUNCTIONS_INFO: bool = False
    DO_INCLUDE_GUARDRAILS_INFO: bool = False

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.API_CORS_ORIGINS.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
