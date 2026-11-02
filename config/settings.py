from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} должен быть целым числом") from exc


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name, str(default))
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} должен быть числом") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    vk_token: str = os.getenv("VK_TOKEN", "").strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.getenv(
        "OPENAI_BASE_URL", "https://foundation-models.api.cloud.ru/v1"
    ).rstrip("/")
    openai_model: str = os.getenv(
        "OPENAI_MODEL", "deepseek-ai/DeepSeek-V4-Pro"
    ).strip()
    temperature: float = _float_env("TEMPERATURE", 0.8)
    max_tokens: int = _int_env("MAX_TOKENS", 1000)
    max_context_messages: int = _int_env("MAX_CONTEXT_MESSAGES", 20)
    max_stored_messages: int = _int_env("MAX_STORED_MESSAGES", 100)
    request_timeout_seconds: int = _int_env("REQUEST_TIMEOUT_SECONDS", 120)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    users_dir: Path = PROJECT_ROOT / os.getenv("USERS_DIR", "users")

    def validate(self) -> None:
        missing = []
        if not self.vk_token:
            missing.append("VK_TOKEN")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if missing:
            raise RuntimeError(
                "Не заполнены обязательные переменные окружения: " + ", ".join(missing)
            )
        if self.max_context_messages < 1:
            raise RuntimeError("MAX_CONTEXT_MESSAGES должен быть больше нуля")
        if self.max_stored_messages < self.max_context_messages:
            raise RuntimeError(
                "MAX_STORED_MESSAGES не может быть меньше MAX_CONTEXT_MESSAGES"
            )


settings = Settings()

