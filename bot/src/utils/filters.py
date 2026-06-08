import logging
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from typing import Union, Dict, Any

from src.models.user import User
from src.utils.db import get_user
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

class IsRootFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        if not user.is_root:
            logger.warning(f"Отказ в доступе (Root): Пользователь {user.telegram_id} попытался выполнить root-действие.")
            if isinstance(event, CallbackQuery):
                await event.answer(TEXTS["messages"]["common"]["no_rights"], show_alert=True)
            return False
        return True
    
class isAdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        if not user.is_admin:
            logger.warning(f"Отказ в доступе (Admin): Пользователь {user.telegram_id} попытался выполнить админ-действие.")
            if isinstance(event, CallbackQuery):
                await event.answer(TEXTS["messages"]["common"]["no_rights"], show_alert=True)
            return False
        return True

class TargetUserFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> Union[bool, Dict[str, Any]]:
        try:
            target_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка парсинга target_id в фильтре: {e}")
            return False

        target_user = await get_user(target_id)
        if not target_user:
            logger.warning(f"TargetUserFilter: Пользователь {target_id} не найден в БД.")
            await callback.answer(TEXTS["messages"]["common"]["user_not_found"], show_alert=True)
            return False
            
        return {"target_user": target_user}