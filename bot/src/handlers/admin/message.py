from aiogram import Router, F, types
from aiogram.filters import Command
from typing import Optional, List
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.client.bot import Bot
from aiogram.types import Message

from src.models.user import User
from src.utils.config import settings
from src.utils.filters import isAdminFilter
from src.utils.db import get_users
from src.keyboards.admin.inline import get_users_list_keyboard, get_participate_keyboard
from src.keyboards.admin.inline import get_confirm_tender_keyboard, get_tenders_menu
from src.states.admin_states import CreateTender
from src.utils.db import get_tender, save_tender
from src.states.admin_states import EditTender

router = Router()

#ЮЗЕРЫ
@router.message(F.text == "👤 Участники", isAdminFilter())
async def admin_view_participants(message: types.Message):
    all_users = await get_users()
    filtered_users = [
    u for u in all_users 
    if u.telegram_id != message.from_user.id and not u.is_admin and not u.is_root]
    if not filtered_users or len(filtered_users) == 0:
        await message.answer("👤 В базе пока нет других участников.")
        return
    
    await message.answer(
        "👤 Список участников проекта: \nВыберите пользователя для управления:",
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="Markdown"
    )

#ТЕНДЕРЫ
@router.message(F.text == "📢 Тендеры", isAdminFilter())
async def admin_open_tenders_menu(message: types.Message):
    await message.answer(
        "📢 Управление тендерамиn\nВыберите нужное действие в меню ниже:",
        reply_markup=get_tenders_menu(),
        parse_mode="Markdown"
    )

@router.message(CreateTender.waiting_for_text, F.text, isAdminFilter())
async def process_tender_text(message: types.Message, state: FSMContext):
    await state.update_data(tender_text=message.text)
    await state.set_state(CreateTender.waiting_for_confirmation)
    preview_text = f"📋 Проверьте информацию перед публикацией:\n\n{message.text}"
    await message.answer(preview_text, reply_markup=get_confirm_tender_keyboard())

@router.message(EditTender.waiting_for_new_text, F.text, isAdminFilter())
async def save_new_tender_text(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    tender_id = data.get("edit_tender_id")
    
    if not tender_id:
        await state.clear()
        return
        
    tender = await get_tender(tender_id)
    if not tender:
        await message.answer("❌ Ошибка: Тендер не найден.")
        await state.clear()
        return
        
    # 1. Обновляем текст в базе данных
    tender.text = message.text
    await save_tender(tender)
    
    # 2. Пытаемся обновить пост в канале (если он там есть)
    if tender.channel_message_id:
        try:
            bot_info = await bot.get_me()
            channel_post = f"💼 Тендер №{tender.tender_id}\n\n{tender.text}"
            
            await bot.edit_message_text(
                chat_id=settings.CHANNEL_ID,
                message_id=tender.channel_message_id,
                text=channel_post,
                reply_markup=get_participate_keyboard(tender.tender_id, bot_info.username)
            )
        except Exception as e:
            await message.answer(f"⚠️ Текст в базе обновлен, но пост в канале изменить не удалось (возможно, он был удален): {e}")
            
    await message.answer(f"✅ Текст тендера #{tender_id} успешно обновлен!")
    await state.clear()