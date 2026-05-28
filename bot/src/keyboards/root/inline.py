from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

from src.models.user import User

def get_users_list_keyboard(users: Optional[List[User]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for user in users:
        display_name = f"{user.nickname} (@{user.username})" if user.username else user.username or user.nickname
        if user.is_banned:
            display_name += " 🚫"
            
        builder.button(text=display_name, callback_data=f"root_view_user:{user.telegram_id}")
        
    builder.adjust(1)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="root_back_to_menu")
    )
    return builder.as_markup()

def get_user_manage_keyboard(user_id: int, is_admin: bool, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ban_text = "🟢 Разбанить" if is_banned else "🚫 Забанить"
    admin_text = "⬇️ Забрать админку" if is_admin else "⬆️ Сделать админом"
    
    builder.button(text=ban_text, callback_data=f"root_toggle_ban:{user_id}")
    builder.button(text=admin_text, callback_data=f"root_toggle_admin:{user_id}")
    builder.button(text="⬅️ К списку участников", callback_data="root_back_to_users_list")
    
    builder.adjust(1)
    return builder.as_markup()

