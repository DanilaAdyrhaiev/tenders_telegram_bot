from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from src.models.user import User
from .db import get_user, save_user, get_users_count

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

            # Создаем модель строго по твоим полям
            user_obj = User(
                telegram_id=from_user.id,
                username=from_user.username,
                nickname=f"Пользователь #{users_count + 1}",
                is_admin=False,
                is_banned=False
            )
            # Сохраняем в TinyDB
            await save_user(user_obj)

        if user_obj.is_banned:
            if isinstance(event, Message):
                await event.answer("Вы заблокированы в этом боте.")
            return
        
        data["user"] = user_obj
        return await handler(event, data)