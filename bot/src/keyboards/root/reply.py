import logging
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

def get_root_reply_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["admin"]["tenders_menu"])
    builder.button(text=TEXTS["buttons"]["root"]["users_menu"])
    builder.button(text=TEXTS["buttons"]["root"]["download_db"])
    builder.adjust(1, 1)
    return builder.as_markup(
        resize_keyboard=True, 
        input_field_placeholder="Выберите действие..."
    )