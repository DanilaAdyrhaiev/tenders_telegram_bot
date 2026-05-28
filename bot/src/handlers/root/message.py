from aiogram import Router, F, types
from aiogram.filters import Command
from typing import Optional, List
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.client.bot import Bot
from aiogram.types import Message

from src.models.user import User
from src.utils.config import settings
from src.utils.db import save_user, get_users
from src.keyboards.root.inline import get_users_list_keyboard
from src.keyboards.root.reply import get_root_reply_menu
from src.utils.filters import IsRootFilter


router = Router()

@router.message(F.text == settings.ROOT_KEY)
async def get_root(message: Message, user: User):
    modify_user = user
    modify_user.is_root = True
    modify_user.is_admin = True
    await save_user(modify_user)
    await message.answer("Вы получили root права", reply_markup=get_root_reply_menu())

@router.message(F.text == "👥 Участники", IsRootFilter())
async def view_participants(message: types.Message):    
    all_users = await get_users()
    filtered_users = [u for u in all_users if u.telegram_id != message.from_user.id]

    if not filtered_users:
        await message.answer("👥 В базе пока нет других участников.")
        return
    
    await message.answer(
        "👥 Список участников проекта: \nВыберите пользователя для управления:",
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="Markdown"
    )