# VK AI Assistant (VKBottle + Gemini + ProxyAPI)

Production-ready каркас интеллектуального AI-ассистента внутри VK-бота с:
- многодиалоговым режимом;
- краткосрочной памятью в JSON;
- переключением ролей общения;
- интеграцией Gemini через ProxyAPI и Google GenAI SDK.

## Изученная документация

- ProxyAPI OpenAI-compatible: [proxyapi.ru/docs/openai-compatible-api](https://proxyapi.ru/docs/openai-compatible-api)
- Google GenAI Python SDK: [googleapis-python-genai-70.mintlify.app/api/chats/create](https://googleapis-python-genai-70.mintlify.app/api/chats/create)
- VKBottle keyboards: [vkbottle.readthedocs.io/ru/v4.x/tools/keyboard](https://vkbottle.readthedocs.io/ru/v4.x/tools/keyboard/)
- VK API keyboards: [dev.vk.com/ru/api/bots/development/keyboard](https://dev.vk.com/ru/api/bots/development/keyboard)

## Архитектурная схема

```text
VK User
  |
  v
VKBottle Bot (bot.py)
  |
  +--> Handlers (bot/handlers/chat_handlers.py)
          |
          +--> DialogService (services/dialog_service.py)
          |       |
          |       +--> MemoryService (services/memory_service.py)
          |               |
          |               +--> JsonStorage (storage/json_storage.py)
          |                       |
          |                       +--> users/<user_id>.json
          |
          +--> AIService (services/ai_service.py)
                  |
                  +--> Google GenAI SDK -> ProxyAPI Google endpoint -> Gemini model
```

## Структура проекта

```text
.
├── bot.py
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py
├── bot/
│   ├── app.py
│   └── handlers/
│       └── chat_handlers.py
├── models/
│   └── chat_models.py
├── services/
│   ├── ai_service.py
│   ├── dialog_service.py
│   └── memory_service.py
├── storage/
│   └── json_storage.py
├── keyboards/
│   └── menu_keyboards.py
├── utils/
│   ├── logger.py
│   └── typing_status.py
└── users/
    └── .gitkeep
```

## JSON-хранилище состояния

Для каждого пользователя создается файл `users/<user_id>.json`:

```json
{
  "user_id": 123456789,
  "active_dialog_id": "uuid",
  "settings": {
    "model": "gemini-2.5-flash",
    "max_history_messages": 100
  },
  "dialogs": [
    {
      "dialog_id": "uuid",
      "title": "Диалог 1",
      "mode": "programmer",
      "created_at": "2026-08-06T17:00:00+00:00",
      "messages": [
        {
          "role": "user",
          "content": "Привет",
          "timestamp": "2026-08-06T17:01:00+00:00"
        },
        {
          "role": "assistant",
          "content": "Привет! Чем помочь?",
          "timestamp": "2026-08-06T17:01:01+00:00"
        }
      ]
    }
  ]
}
```

## Режимы общения (system prompts)

Реализовано 5 режимов:
- Обычный помощник
- Программист
- Преподаватель
- Бизнес-консультант
- Дружелюбный собеседник

Режим хранится внутри конкретного диалога, поэтому смена стиля влияет только на текущий диалог.

## Как формируется контекст

При каждом запросе:
1. Берутся последние 100 сообщений активного диалога.
2. `system_prompt` берется из текущего режима диалога.
3. В Gemini отправляются роли:
   - `user` (сообщения пользователя)
   - `assistant` -> преобразуется в `model` для Google GenAI
   - `system` передается через `GenerateContentConfig(system_instruction=...)`
4. Добавляется текущее сообщение пользователя.

## Интеграция Gemini через ProxyAPI (Google GenAI SDK)

`AIService` создает клиент:
- `api_key` = `PROXY_API_KEY`
- `base_url` = `https://api.proxyapi.ru/google`
- модель настраивается через `.env` (`GEMINI_MODEL`)

Это позволяет централизованно менять модель и при необходимости подключить другие AI-провайдеры через новый сервис-адаптер.

## VK UX и кнопки

### Главное меню
- Новый диалог
- Список диалогов
- Настройки
- Сменить режим
- Помощь

### Список диалогов (inline callback)
- Кнопка переключения на диалог
- Кнопка удаления диалога

### Настройки
- Выбор режима общения
- Информация о модели
- Очистка истории

## Дополнительные функции

- Полная асинхронность (`async/await`)
- Статус `"Бот думает..."`
- Имитация набора (`messages.set_activity(type="typing")`)
- Ограничение длины пользовательского сообщения
- Защита от пустых сообщений
- Обработка ошибок сети/API и fallback-ответ
- Логирование

## Установка и запуск

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Создать `.env` по образцу:
```bash
cp .env.example .env
```

3. Заполнить значения:
- `VK_TOKEN`
- `PROXY_API_KEY`

4. Запуск:
```bash
python bot.py
```

## Пример запроса к Gemini через ProxyAPI (совместимый формат)

```bash
curl "https://openai.api.proxyapi.ru/v1/chat/completions" \
  -H "Authorization: Bearer $PROXY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini/gemini-2.0-flash",
    "messages": [{"role":"user","content":"Привет!"}]
  }'
```

## Масштабирование

- Добавить `UserLockManager` (пер-пользовательные `asyncio.Lock`) для защиты от гонок записи JSON.
- Вынести storage в интерфейс (`StorageProtocol`) и подключать новые типы хранилищ без изменений сервисов.
- Добавить мониторинг latency/ошибок Gemini и метрики активности диалогов.
- Включить streaming-ответы (частичные сообщения) при необходимости.
- Добавить очереди задач для heavy-нагрузки и retry с backoff.
