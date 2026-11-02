from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageModel(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: float = Field(default_factory=time.time)


class DialogModel(BaseModel):
    id: str
    name: str
    mode: str = "Обычный помощник"
    messages: list[MessageModel] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class UserModel(BaseModel):
    user_id: int
    active_dialog_id: str = "default"
    dialogs: dict[str, DialogModel] = Field(
        default_factory=lambda: {
            "default": DialogModel(id="default", name="Основной диалог")
        }
    )
    settings: dict[str, Any] = Field(default_factory=dict)

