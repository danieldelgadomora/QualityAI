from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).parent.parent        # BE-AI/
_AGENT_DIR = _BASE_DIR.parent / "modulo1_requirements_refiner"

# Priority: BE-AI/.env > qualityai-modulo1/.env
_local_env = _BASE_DIR / ".env"
_agent_env = _AGENT_DIR / ".env"
_ENV_FILE = str(_local_env) if _local_env.exists() else str(_agent_env)


class Settings(BaseSettings):
    groq_api_key: str
    max_concurrent_jobs: int = 3
    agent_module_path: str = str(_AGENT_DIR)

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
