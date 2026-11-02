from __future__ import annotations

import logging

from vkbottle.bot import Bot

from bot.handlers import labeler
from config.settings import settings
from utils.logger import setup_logging


def main() -> None:
    setup_logging()
    settings.validate()
    logger = logging.getLogger("vk_ai_bot")
    logger.info(
        "Запуск VK AI Bot: model=%s, context=%s, timeout=%ss",
        settings.openai_model,
        settings.max_context_messages,
        settings.request_timeout_seconds,
    )
    bot = Bot(token=settings.vk_token)
    bot.labeler.load(labeler)
    bot.run_forever()


if __name__ == "__main__":
    main()

