from __future__ import annotations

import time
import uuid

from config.settings import settings
from models.schemas import DialogModel, MessageModel, UserModel


class DialogService:
    @staticmethod
    def active(user: UserModel) -> DialogModel:
        if user.active_dialog_id not in user.dialogs:
            user.active_dialog_id = next(iter(user.dialogs), "default")
        if user.active_dialog_id not in user.dialogs:
            user.dialogs["default"] = DialogModel(
                id="default", name="Основной диалог"
            )
            user.active_dialog_id = "default"
        return user.dialogs[user.active_dialog_id]

    @staticmethod
    def create(user: UserModel) -> DialogModel:
        dialog_id = uuid.uuid4().hex[:8]
        dialog = DialogModel(
            id=dialog_id, name=f"Диалог {len(user.dialogs) + 1}"
        )
        user.dialogs[dialog_id] = dialog
        user.active_dialog_id = dialog_id
        return dialog

    @staticmethod
    def select(user: UserModel, dialog_id: str) -> DialogModel | None:
        dialog = user.dialogs.get(dialog_id)
        if dialog:
            user.active_dialog_id = dialog_id
        return dialog

    @staticmethod
    def delete(user: UserModel, dialog_id: str) -> bool:
        if dialog_id not in user.dialogs:
            return False
        del user.dialogs[dialog_id]
        if not user.dialogs:
            user.dialogs["default"] = DialogModel(
                id="default", name="Основной диалог"
            )
        if user.active_dialog_id == dialog_id:
            user.active_dialog_id = next(iter(user.dialogs))
        return True

    @staticmethod
    def rename(user: UserModel, dialog_id: str, name: str) -> bool:
        dialog = user.dialogs.get(dialog_id)
        clean_name = " ".join(name.split())[:40]
        if not dialog or not clean_name:
            return False
        dialog.name = clean_name
        dialog.updated_at = time.time()
        return True

    @staticmethod
    def set_mode(user: UserModel, mode: str) -> bool:
        from services.ai_service import SYSTEM_PROMPTS

        if mode not in SYSTEM_PROMPTS:
            return False
        dialog = DialogService.active(user)
        dialog.mode = mode
        dialog.messages.clear()
        dialog.updated_at = time.time()
        return True

    @staticmethod
    def clear_history(user: UserModel) -> None:
        dialog = DialogService.active(user)
        dialog.messages.clear()
        dialog.updated_at = time.time()

    @staticmethod
    def add_message(user: UserModel, role: str, content: str) -> None:
        dialog = DialogService.active(user)
        dialog.messages.append(MessageModel(role=role, content=content))
        dialog.messages = dialog.messages[-settings.max_stored_messages :]
        dialog.updated_at = time.time()


dialog_service = DialogService()

