from models.schemas import UserModel
from services.dialog_service import DialogService


def test_dialog_lifecycle():
    user = UserModel(user_id=7)
    created = DialogService.create(user)
    assert user.active_dialog_id == created.id
    assert DialogService.rename(user, created.id, " Рабочий   чат ")
    assert created.name == "Рабочий чат"
    assert DialogService.delete(user, created.id)
    assert user.active_dialog_id in user.dialogs


def test_models_do_not_share_mutable_defaults():
    first = UserModel(user_id=1)
    second = UserModel(user_id=2)
    DialogService.add_message(first, "user", "Привет")
    assert len(DialogService.active(first).messages) == 1
    assert DialogService.active(second).messages == []

