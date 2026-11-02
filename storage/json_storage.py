from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path

import aiofiles

from config.settings import settings
from models.schemas import UserModel


logger = logging.getLogger(__name__)


class JSONStorage:
    def __init__(self, users_dir: Path) -> None:
        self.users_dir = users_dir
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self._locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _path(self, user_id: int) -> Path:
        return self.users_dir / f"{user_id}.json"

    async def _load_unlocked(self, user_id: int) -> UserModel:
        path = self._path(user_id)
        if not path.exists():
            return UserModel(user_id=user_id)

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as file:
                payload = await file.read()
            return UserModel.model_validate_json(payload)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            backup = path.with_suffix(f".corrupt-{int(time.time())}.json")
            try:
                os.replace(path, backup)
            except OSError:
                logger.exception("Не удалось сохранить повреждённый файл %s", path)
            logger.error("Повреждён JSON пользователя %s: %s", user_id, exc)
            return UserModel(user_id=user_id)

    async def load_user(self, user_id: int) -> UserModel:
        async with self._locks[user_id]:
            return await self._load_unlocked(user_id)

    async def save_user(self, user: UserModel) -> None:
        async with self._locks[user.user_id]:
            await self._save_unlocked(user)

    async def update_user(self, user_id: int, mutator) -> UserModel:
        async with self._locks[user_id]:
            user = await self._load_unlocked(user_id)
            mutator(user)
            await self._save_unlocked(user)
            return user

    async def _save_unlocked(self, user: UserModel) -> None:
        path = self._path(user.user_id)
        temporary = path.with_suffix(".tmp")
        async with aiofiles.open(temporary, "w", encoding="utf-8") as file:
            await file.write(user.model_dump_json(indent=2))
        os.replace(temporary, path)


storage = JSONStorage(settings.users_dir)

