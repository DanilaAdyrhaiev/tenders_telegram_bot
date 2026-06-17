import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.client.bot import Bot
from aiogram.types import Message
import html

from src.models.user import User
from src.utils.config import settings
from src.utils.filters import isAdminFilter
from src.utils.db import get_users, get_tender, save_tender, get_user, save_user
from src.keyboards.admin.inline import (
    get_users_list_keyboard, get_participate_keyboard, 
    get_confirm_tender_keyboard, get_tenders_menu
)
from src.states.admin_states import CreateTender, EditTender, EditUser
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == TEXTS["buttons"]["admin"]["users_menu"], isAdminFilter())
async def admin_view_participants(message: types.Message, user: User):
    logger.info(f"Админ {user.telegram_id} открыл список участников.")
    all_users = await get_users()
    filtered_users = [
        u for u in all_users 
        if u.telegram_id != message.from_user.id and not u.is_admin and not u.is_root
    ]
    
    if not filtered_users or len(filtered_users) == 0:
        await message.answer(TEXTS["messages"]["admin"]["users_empty"])
        return
    
    await message.answer(
        TEXTS["messages"]["admin"]["users_list"],
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="HTML"
    )

@router.message(F.text == TEXTS["buttons"]["admin"]["tenders_menu"], isAdminFilter())
async def admin_open_tenders_menu(message: types.Message, user: User):
    logger.info(f"Админ {user.telegram_id} открыл меню управления тендерами.")
    await message.answer(
        TEXTS["messages"]["admin"]["tenders_menu"],
        reply_markup=get_tenders_menu(),
        parse_mode="HTML"
    )

@router.message(CreateTender.waiting_for_text, F.text, isAdminFilter())
async def process_tender_text(message: types.Message, state: FSMContext, user: User):
    safe_text = html.escape(message.text, quote=False)
    await state.update_data(tender_text=safe_text)
    await state.set_state(CreateTender.waiting_for_confirmation)
    
    logger.info(f"Админ {user.telegram_id} ввел текст для нового тендера.")
    preview_text = TEXTS["messages"]["admin"]["preview_publication"].format(text=safe_text)
    await message.answer(preview_text, reply_markup=get_confirm_tender_keyboard(), parse_mode="HTML")

@router.message(EditTender.waiting_for_new_text, F.text, isAdminFilter())
async def save_new_tender_text(message: types.Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    tender_id = data.get("edit_tender_id")
    
    if not tender_id:
        logger.warning(f"Ошибка стейта при редактировании тендера админом {user.telegram_id}")
        await state.clear()
        return
        
    tender = await get_tender(tender_id)
    if not tender:
        logger.error(f"Админ {user.telegram_id} пытался отредактировать несуществующий тендер #{tender_id}")
        await message.answer(TEXTS["messages"]["admin"]["tender_not_found"])
        await state.clear()
        return
        
    safe_text = html.escape(message.text, quote=False)
    tender.text = safe_text
    await save_tender(tender)
    logger.info(f"Админ {user.telegram_id} успешно обновил текст в БД для тендера #{tender_id}")
    
    if tender.channel_message_id:
        try:
            bot_info = await bot.get_me()
            channel_post = TEXTS["messages"]["user"]["channel_post"].format(
                tender_id=tender.tender_id, text=tender.text
            )
            
            await bot.edit_message_text(
                chat_id=settings.CHANNEL_ID,
                message_id=tender.channel_message_id,
                text=channel_post,
                reply_markup=get_participate_keyboard(tender.tender_id, bot_info.username),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка редактирования поста тендера #{tender_id} в канале: {e}")
            await message.answer(TEXTS["messages"]["admin"]["edit_channel_error"].format(error=html.escape(str(e))))
            
    await message.answer(TEXTS["messages"]["admin"]["edit_success"].format(tender_id=tender_id), parse_mode="HTML")
    await state.clear()

@router.message(StateFilter(EditUser.waiting_for_new_name), F.text, isAdminFilter())
async def process_new_user_name(message: types.Message, state: FSMContext, user: User):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    
    target_user = await get_user(target_user_id)
    if target_user:
        target_user.nickname = html.escape(message.text, quote=False)
        await save_user(target_user)
        
        success_text = TEXTS["messages"]["admin"]["rename_success"].format(
            nickname=target_user.nickname
        )
        await message.answer(success_text, parse_mode="HTML")
    else:
        error_text = TEXTS["messages"]["admin"]["rename_error"]
        await message.answer(error_text)
        
    await state.clear()