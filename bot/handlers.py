from __future__ import annotations

import json
import logging

from vkbottle.bot import BotLabeler, Message

from config.settings import settings
from keyboards.menus import (
    dialog_actions_keyboard,
    dialogs_keyboard,
    main_keyboard,
    modes_keyboard,
    settings_keyboard,
)
from services.ai_service import SYSTEM_PROMPTS, ai_service
from services.dialog_service import dialog_service
from storage.json_storage import storage
from utils.text import split_message


logger = logging.getLogger(__name__)
labeler = BotLabeler()

HOME_TEXTS = {"начать", "старт", "привет", "помощь", "❓ помощь", "🏠 главное меню"}


def _payload(message: Message) -> dict:
    raw = getattr(message, "payload", None)
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


async def _typing(message: Message) -> None:
    try:
        await message.ctx_api.messages.set_activity(
            peer_id=message.peer_id, type="typing"
        )
    except Exception:
        logger.debug("Не удалось включить typing для peer_id=%s", message.peer_id)


@labeler.message(text=list(HOME_TEXTS))
async def home_handler(message: Message) -> None:
    await message.answer(
        "🤖 Я AI-помощник LogicPulse для ВКонтакте.\n\n"
        "Создавайте независимые диалоги, переключайте роли и возвращайтесь к "
        "сохранённому контексту в любой момент.",
        keyboard=main_keyboard(),
    )


@labeler.message(text="➕ Новый диалог")
async def new_dialog_handler(message: Message) -> None:
    created = None

    def mutate(user):
        nonlocal created
        created = dialog_service.create(user)

    await storage.update_user(message.from_id, mutate)
    await message.answer(
        f"✅ Создан и открыт «{created.name}».",
        keyboard=dialog_actions_keyboard(created.id),
    )


@labeler.message(text="💬 Мои диалоги")
async def dialogs_handler(message: Message) -> None:
    user = await storage.load_user(message.from_id)
    lines = ["💬 Ваши диалоги:"]
    for dialog in user.dialogs.values():
        marker = "●" if dialog.id == user.active_dialog_id else "○"
        lines.append(f"{marker} {dialog.name} · {dialog.mode}")
    await message.answer("\n".join(lines), keyboard=dialogs_keyboard(user))


@labeler.message(text="🎭 Сменить режим")
async def mode_menu_handler(message: Message) -> None:
    await message.answer(
        "Выберите роль. История только текущего диалога будет очищена:",
        keyboard=modes_keyboard(list(SYSTEM_PROMPTS)),
    )


@labeler.message(text=list(SYSTEM_PROMPTS))
async def set_mode_handler(message: Message) -> None:
    await storage.update_user(
        message.from_id, lambda user: dialog_service.set_mode(user, message.text)
    )
    await message.answer(
        f"✅ Режим изменён на «{message.text}». Контекст текущего диалога очищен.",
        keyboard=main_keyboard(),
    )


@labeler.message(text="⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    user = await storage.load_user(message.from_id)
    dialog = dialog_service.active(user)
    await message.answer(
        "⚙️ Настройки текущего диалога\n\n"
        f"Диалог: {dialog.name}\n"
        f"Режим: {dialog.mode}\n"
        f"Модель: {settings.openai_model}\n"
        f"Контекст: {settings.max_context_messages} сообщений\n"
        f"Сохранено: {len(dialog.messages)} сообщений",
        keyboard=settings_keyboard(),
    )


@labeler.message(text="🧹 Очистить историю")
async def clear_handler(message: Message) -> None:
    await storage.update_user(
        message.from_id, lambda user: dialog_service.clear_history(user)
    )
    await message.answer("✅ История текущего диалога очищена.", keyboard=main_keyboard())


@labeler.message()
async def universal_handler(message: Message) -> None:
    payload = _payload(message)
    action = payload.get("action")
    dialog_id = str(payload.get("id", ""))

    if action == "select_dialog":
        selected = None

        def select(user):
            nonlocal selected
            selected = dialog_service.select(user, dialog_id)

        await storage.update_user(message.from_id, select)
        if selected:
            await message.answer(
                f"✅ Открыт диалог «{selected.name}». Продолжайте общение.",
                keyboard=dialog_actions_keyboard(selected.id),
            )
        else:
            await message.answer("Диалог не найден.", keyboard=main_keyboard())
        return

    if action == "delete_dialog":
        deleted = False

        def delete(user):
            nonlocal deleted
            deleted = dialog_service.delete(user, dialog_id)

        user = await storage.update_user(message.from_id, delete)
        text = "✅ Диалог удалён." if deleted else "Диалог уже не существует."
        await message.answer(text, keyboard=dialogs_keyboard(user))
        return

    if action == "rename_dialog":
        def prepare(user):
            if dialog_id in user.dialogs:
                user.settings["rename_dialog_id"] = dialog_id

        await storage.update_user(message.from_id, prepare)
        await message.answer(
            "Введите новое название диалога (до 40 символов).",
            keyboard=main_keyboard(),
        )
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer(
            "Пока я понимаю только текстовые сообщения.", keyboard=main_keyboard()
        )
        return

    renamed = False

    def maybe_rename(user):
        nonlocal renamed
        pending_id = user.settings.pop("rename_dialog_id", None)
        if pending_id:
            renamed = dialog_service.rename(user, pending_id, text)

    user = await storage.update_user(message.from_id, maybe_rename)
    if renamed:
        await message.answer("✅ Диалог переименован.", keyboard=dialogs_keyboard(user))
        return

    await _typing(message)

    user = await storage.update_user(
        message.from_id,
        lambda item: dialog_service.add_message(item, "user", text),
    )
    dialog = dialog_service.active(user)
    answer = await ai_service.generate_response(dialog)
    await storage.update_user(
        message.from_id,
        lambda item: dialog_service.add_message(item, "assistant", answer),
    )

    parts = split_message(answer)
    for index, part in enumerate(parts):
        await message.answer(part, keyboard=main_keyboard() if index == len(parts) - 1 else None)

