from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from typing import Union, Dict, Any

from src.models.user import User
from src.utils.db import get_user

class IsRootFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        if not user.is_root:
            if isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет прав для этого действия.", show_alert=True)
            elif isinstance(event, Message):
                pass
            return False
        return True
    
class isAdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        if not user.is_admin:
            if isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет прав для этого действия.", show_alert=True)
            elif isinstance(event, Message):
                pass
            return False
        return True


class TargetUserFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> Union[bool, Dict[str, Any]]:
        try:
            target_id = int(callback.data.split(":")[1])
        except (IndexError, ValueError):
            return False

        target_user = await get_user(target_id)
        if not target_user:
            await callback.answer("❌ Пользователь не найден в базе.", show_alert=True)
            return False
        return {"target_user": target_user}