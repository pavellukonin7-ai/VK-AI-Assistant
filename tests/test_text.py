from utils.text import split_message


def test_short_message_is_unchanged():
    assert split_message("Привет", limit=10) == ["Привет"]


def test_long_message_is_split_without_loss():
    text = "слово " * 100
    parts = split_message(text, limit=50)
    assert all(len(part) <= 50 for part in parts)
    assert "".join(parts).replace(" ", "") == text.replace(" ", "")

