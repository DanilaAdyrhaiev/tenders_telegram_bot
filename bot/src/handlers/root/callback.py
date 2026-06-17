import logging
import html
from aiogram import Router, F, types
from aiogram.client.bot import Bot
from aiogram.types import ReplyKeyboardRemove


from src.models.user import User
from src.utils.db import save_user, get_users
from src.keyboards.root.inline import get_user_manage_keyboard, get_users_list_keyboard
from src.keyboards.admin.reply import get_admin_reply_menu
from src.utils.filters import IsRootFilter, TargetUserFilter
from src.utils.lexicon import TEXTS
from src.utils.config import settings

logger = logging.getLogger(__name__)
router = Router()

def get_user_profile_text(target_user: User, is_updated: bool = False) -> str:
    status = TEXTS["messages"]["profile"]["status_banned"] if target_user.is_banned else TEXTS["messages"]["profile"]["status_active"]
    is_admin_str = TEXTS["messages"]["profile"]["yes"] if target_user.is_admin else TEXTS["messages"]["profile"]["no"]
    title = TEXTS["messages"]["profile"]["title_updated"] if is_updated else TEXTS["messages"]["profile"]["title_normal"]
    
    return TEXTS["messages"]["profile"]["body"].format(
        title=title,
        nickname=html.escape(target_user.nickname),
        telegram_id=target_user.telegram_id,
        username=html.escape(target_user.username or 'отсутствует'),
        is_admin=is_admin_str,
        status=status
    )

@router.callback_query(F.data.startswith("root_view_user:"), IsRootFilter(), TargetUserFilter())
async def process_view_user(callback: types.CallbackQuery, target_user: User):
    await callback.message.edit_text(
        text=get_user_profile_text(target_user),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("root_toggle_admin:"), IsRootFilter(), TargetUserFilter())
async def toggle_admin(callback: types.CallbackQuery, target_user: User, bot: Bot):
    target_user.is_admin = not target_user.is_admin
    await save_user(target_user)
    alert_msg = TEXTS["messages"]["root"]["admin_granted_alert"] if target_user.is_admin else TEXTS["messages"]["root"]["admin_revoked_alert"]
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="HTML"
    )

    try:
        if target_user.is_admin:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=TEXTS["messages"]["root"]["notify_made_admin"],
                reply_markup=get_admin_reply_menu(), parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text=TEXTS["messages"]["root"]["notify_removed_admin"],
                reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление об изменении прав пользователю {target_user.telegram_id}: {e}")

@router.callback_query(F.data.startswith("root_toggle_ban:"), IsRootFilter(), TargetUserFilter())
async def toggle_ban(callback: types.CallbackQuery, target_user: User, bot: Bot): # <-- Добавили bot: Bot
    target_user.is_banned = not target_user.is_banned
    await save_user(target_user)
    
    # --- НОВАЯ ЛОГИКА ДЛЯ ROOT: Удаление из канала ---
    try:
        if target_user.is_banned:
            await bot.ban_chat_member(chat_id=settings.CHANNEL_ID, user_id=target_user.telegram_id)
        else:
            await bot.unban_chat_member(chat_id=settings.CHANNEL_ID, user_id=target_user.telegram_id, only_if_banned=True)
    except Exception as e:
        logger.error(f"Не удалось изменить статус пользователя {target_user.telegram_id} в канале (Root): {e}")
    # ------------------------------------------------

    alert_msg = TEXTS["messages"]["root"]["ban_alert"] if target_user.is_banned else TEXTS["messages"]["root"]["unban_alert"]
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "root_back_to_users_list", IsRootFilter())
async def root_process_back_to_users(callback: types.CallbackQuery):
    all_users = await get_users()
    # Рут видит всех пользователей, кроме самого себя
    filtered_users = [u for u in all_users if u.telegram_id != callback.from_user.id]
    
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["users_list"],
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "root_back_to_menu", IsRootFilter())
async def root_process_close_inline(callback: types.CallbackQuery):
    # Эта функция закроет меню при нажатии "Назад" в самом списке
    await callback.message.delete()
    await callback.answer()
