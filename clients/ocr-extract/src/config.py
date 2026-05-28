import os

from fastapi import HTTPException


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"{name} must be configured")
    return value


def litellm_base_url() -> str:
    return os.getenv("LITELLM_BASE_URL", "http://litellm:4000/v1").rstrip("/")


def litellm_api_key() -> str:
    return os.getenv("LITELLM_API_KEY", "sk-local-litellm")
