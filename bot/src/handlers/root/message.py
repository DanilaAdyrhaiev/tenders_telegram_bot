import logging
from aiogram import Router, F, types
from aiogram.types import Message
import os
from aiogram.types import FSInputFile
from src.utils.export import export_db_to_excel

from src.models.user import User
from src.utils.config import settings
from src.utils.db import save_user, get_users
from src.keyboards.root.inline import get_users_list_keyboard
from src.keyboards.root.reply import get_root_reply_menu
from src.utils.filters import IsRootFilter
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == settings.ROOT_KEY)
async def get_root(message: Message, user: User):
    modify_user = user
    modify_user.is_root = True
    modify_user.is_admin = True
    await save_user(modify_user)
    
    logger.critical(f"ВНИМАНИЕ: Пользователь {user.telegram_id} ({user.nickname}) активировал ROOT-права!")
    
    await message.answer(
        TEXTS["messages"]["root"]["root_granted"], 
        reply_markup=get_root_reply_menu()
    )

@router.message(F.text == TEXTS["buttons"]["root"]["users_menu"], IsRootFilter())
async def view_participants(message: types.Message):    
    logger.info(f"Root {message.from_user.id} запросил список участников.")
    all_users = await get_users()
    filtered_users = [u for u in all_users if u.telegram_id != message.from_user.id]

    if not filtered_users:
        await message.answer(TEXTS["messages"]["admin"]["users_empty"], parse_mode="HTML")
        return
    
    await message.answer(
        TEXTS["messages"]["admin"]["users_list"],
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="HTML"
    )

@router.message(F.text == TEXTS["buttons"]["root"]["download_db"], IsRootFilter())
async def root_download_db(message: types.Message):
    logger.info(f"Root {message.from_user.id} запросил выгрузку БД.")
    
    db_path = "database.json" 
    excel_path = "database.xlsx"
    
    if not os.path.exists(db_path):
        await message.answer(TEXTS["messages"]["root"]["db_not_found"], parse_mode="HTML")
        return
        
    # Генерируем Excel-файл
    export_success = export_db_to_excel(db_path, excel_path)
        
    try:
        # 1. Отправляем оригинальный JSON
        await message.answer_document(
            document=FSInputFile(db_path),
            caption=TEXTS["messages"]["root"]["db_downloaded"],
            parse_mode="HTML"
        )
        
        # 2. Отправляем Excel, если он успешно создался
        if export_success and os.path.exists(excel_path):
            await message.answer_document(
                document=FSInputFile(excel_path),
                caption=TEXTS["messages"]["root"]["db_downloaded_excel"],
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке файлов БД: {e}")
        await message.answer(TEXTS["messages"]["root"]["db_download_error"], parse_mode="HTML")