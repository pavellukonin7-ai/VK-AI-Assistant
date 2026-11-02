from __future__ import annotations

import logging

import httpx2
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from config.settings import settings
from models.schemas import DialogModel


logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "Обычный помощник": (
        "Ты полезный AI-ассистент. Отвечай на русском языке, вежливо, ясно и по делу."
    ),
    "Программист": (
        "Ты senior-разработчик и DevOps-инженер. Давай технически точные ответы, "
        "предлагай безопасную архитектуру и объясняй важные решения."
    ),
    "Преподаватель": (
        "Ты опытный преподаватель. Объясняй от простого к сложному, используй примеры "
        "и проверяй, понятен ли материал."
    ),
    "Бизнес-консультант": (
        "Ты практичный бизнес-консультант. Структурируй выводы, отмечай риски, "
        "метрики и следующий конкретный шаг."
    ),
    "Дружелюбный собеседник": (
        "Ты внимательный и доброжелательный собеседник. Поддерживай естественный "
        "разговор, сохраняя уважительный тон."
    ),
}


class AIService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key or "not-configured",
            base_url=settings.openai_base_url,
            timeout=settings.request_timeout_seconds,
            max_retries=2,
            http_client=httpx2.AsyncClient(
                timeout=settings.request_timeout_seconds,
                trust_env=False,
            ),
        )

    async def generate_response(self, dialog: DialogModel) -> str:
        system_prompt = SYSTEM_PROMPTS.get(
            dialog.mode, SYSTEM_PROMPTS["Обычный помощник"]
        )
        context = dialog.messages[-settings.max_context_messages :]
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(
            {"role": item.role, "content": item.content} for item in context
        )

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
            )
            answer = response.choices[0].message.content
            if not answer:
                return "Не удалось получить текстовый ответ. Попробуйте ещё раз."
            return answer.strip()
        except APITimeoutError:
            logger.warning("Foundation Models API: превышен тайм-аут")
            return "⏳ Модель отвечает дольше обычного. Попробуйте ещё раз через минуту."
        except APIConnectionError:
            logger.exception("Foundation Models API: ошибка соединения")
            return "🌐 Не удалось связаться с AI-сервисом. Попробуйте чуть позже."
        except APIStatusError as exc:
            logger.error("Foundation Models API вернул статус %s", exc.status_code)
            return "⚠️ AI-сервис временно недоступен. Попробуйте позже."
        except Exception:
            logger.exception("Непредвиденная ошибка AI-сервиса")
            return "⚠️ Произошла временная ошибка. Попробуйте ещё раз."


ai_service = AIService()

