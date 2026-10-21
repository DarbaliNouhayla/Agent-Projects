from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    groq_api_key: SecretStr
    groq_primary_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"
    mock_backend_url: str = "http://localhost:8000"
    max_agent_iterations: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
