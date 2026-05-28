from aiogram import Router, F, types
from aiogram.filters import Command
from typing import Optional, List
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.client.bot import Bot
from aiogram.types import ReplyKeyboardRemove

from src.models.user import User
from src.utils.db import save_user, get_user
from src.keyboards.root.inline import get_user_manage_keyboard
from src.keyboards.admin.reply import get_admin_reply_menu
from src.utils.filters import IsRootFilter, TargetUserFilter

router = Router()

def get_user_profile_text(target_user: User, is_updated: bool = False) -> str:
    status = "❌ Заблокирован" if target_user.is_banned else "✅ Активен"
    is_admin_str = "Да" if target_user.is_admin else "Нет"
    
    title = "👤Профиль участника (Статус обновлен!)**" if is_updated else "👤Профиль участника**"
    
    return (
        f"{title}\n\n"
        f"•Никнейм:** {target_user.nickname}\n"
        f"•Telegram ID:** `{target_user.telegram_id}`\n"
        f"•Юзернейм:** @{target_user.username or 'отсутствует'}\n"
        f"•Администратор:** {is_admin_str}\n"
        f"•Статус:** {status}"
    )

@router.callback_query(F.data.startswith("root_view_user:"), IsRootFilter(), TargetUserFilter())
async def process_view_user(callback: types.CallbackQuery, target_user: User):
    await callback.message.edit_text(
        text=get_user_profile_text(target_user),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("root_toggle_admin:"), IsRootFilter(), TargetUserFilter())
async def toggle_admin(callback: types.CallbackQuery, target_user: User, bot: Bot):
    target_user.is_admin = not target_user.is_admin
    await save_user(target_user)

    alert_msg = "✅ Права администратора выданы!" if target_user.is_admin else "❌ Права администратора сняты!"
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="Markdown"
    )

    try:
        if target_user.is_admin:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text="🎉 Вы были назначены администратором бота! Теперь вам доступно новое меню.",
                reply_markup=get_admin_reply_menu()
            )
        else:
            await bot.send_message(
                chat_id=target_user.telegram_id,
                text="ℹ️ Ваши права администратора были отозваны.",
                reply_markup=ReplyKeyboardRemove() 
            )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {target_user.telegram_id}: {e}")


@router.callback_query(F.data.startswith("root_toggle_admin:"), IsRootFilter(), TargetUserFilter())
async def toggle_ban(callback: types.CallbackQuery, target_user: User):
    target_user.is_banned = not target_user.is_banned
    await save_user(target_user)

    alert_msg = "❌ Пользователь заблокирован!" if target_user.is_banned else "✅ Пользователь разблокирован!"
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_admin, target_user.is_banned),
        parse_mode="Markdown"
    )