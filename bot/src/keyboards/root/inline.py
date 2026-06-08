import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from src.models.user import User
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

def get_users_list_keyboard(users: Optional[List[User]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if users:
        for user in users:
            display_name = f"{user.nickname} (@{user.username})" if user.username else user.username or user.nickname
            if user.is_banned:
                display_name += " 🚫"
                
            builder.button(text=display_name, callback_data=f"root_view_user:{user.telegram_id}")
        
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=TEXTS["buttons"]["common"]["back"], callback_data="root_back_to_menu")
    )
    return builder.as_markup()

def get_user_manage_keyboard(user_id: int, is_admin: bool, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ban_text = TEXTS["buttons"]["admin"]["unban"] if is_banned else TEXTS["buttons"]["admin"]["ban"]
    admin_text = TEXTS["buttons"]["root"]["remove_admin"] if is_admin else TEXTS["buttons"]["root"]["make_admin"]
    
    builder.button(text=ban_text, callback_data=f"root_toggle_ban:{user_id}")
    builder.button(text=admin_text, callback_data=f"root_toggle_admin:{user_id}")
    builder.button(text=TEXTS["buttons"]["admin"]["back_to_users"], callback_data="root_back_to_users_list")
    
    builder.adjust(1)
    return builder.as_markup()