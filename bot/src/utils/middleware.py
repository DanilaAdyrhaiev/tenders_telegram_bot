import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from src.models.user import User
from .db import get_user, save_user, get_users_count
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

class UserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:
        
        from_user = None
        if isinstance(event, (Message, CallbackQuery)):
            from_user = event.from_user
            
        if not from_user:
            return await handler(event, data)

        user_obj = await get_user(from_user.id)

        if not user_obj:
            users_count = await get_users_count()
            user_obj = User(
                telegram_id=from_user.id,
                username=from_user.username,
                nickname=f"Пользователь #{users_count + 1}",
                is_admin=False,
                is_banned=False
            )
            await save_user(user_obj)
            logger.info(f"Зарегистрирован новый пользователь: {user_obj.telegram_id} ({user_obj.nickname})")

        if user_obj.is_banned:
            logger.info(f"Заблокированный пользователь {user_obj.telegram_id} попытался использовать бота.")
            if isinstance(event, Message):
                await event.answer(TEXTS["messages"]["common"]["banned_alert"])
            return
        
        data["user"] = user_obj
        return await handler(event, data)