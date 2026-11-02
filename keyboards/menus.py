from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text

from models.schemas import UserModel


def main_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("➕ Новый диалог"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("💬 Мои диалоги"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🎭 Сменить режим"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("⚙️ Настройки"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("❓ Помощь"), color=KeyboardButtonColor.POSITIVE)
    return keyboard.get_json()


def modes_keyboard(modes: list[str]) -> str:
    keyboard = Keyboard(one_time=True, inline=False)
    for index, mode in enumerate(modes):
        keyboard.add(Text(mode), color=KeyboardButtonColor.PRIMARY)
        if index % 2 == 1 and index < len(modes) - 1:
            keyboard.row()
    keyboard.row()
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def settings_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🎭 Сменить режим"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🧹 Очистить историю"), color=KeyboardButtonColor.NEGATIVE)
    keyboard.row()
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def dialogs_keyboard(user: UserModel) -> str:
    keyboard = Keyboard(one_time=True, inline=False)
    for index, dialog in enumerate(list(user.dialogs.values())[:8]):
        marker = "✓ " if dialog.id == user.active_dialog_id else ""
        label = f"{marker}Открыть · {dialog.name}"[:40]
        keyboard.add(
            Text(label, payload={"action": "select_dialog", "id": dialog.id}),
            color=(
                KeyboardButtonColor.POSITIVE
                if dialog.id == user.active_dialog_id
                else KeyboardButtonColor.SECONDARY
            ),
        )
        keyboard.row()
    keyboard.add(Text("➕ Новый диалог"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def dialog_actions_keyboard(dialog_id: str) -> str:
    keyboard = Keyboard(one_time=True, inline=False)
    keyboard.add(
        Text("✏️ Переименовать", payload={"action": "rename_dialog", "id": dialog_id}),
        color=KeyboardButtonColor.SECONDARY,
    )
    keyboard.add(
        Text("🗑 Удалить", payload={"action": "delete_dialog", "id": dialog_id}),
        color=KeyboardButtonColor.NEGATIVE,
    )
    keyboard.row()
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()

