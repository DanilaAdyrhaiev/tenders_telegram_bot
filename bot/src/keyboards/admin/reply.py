from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup

def get_admin_reply_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📢 Тендеры")
    builder.button(text="👤 Участники")
    builder.adjust(1)
    return builder.as_markup(
        resize_keyboard=True, 
        input_field_placeholder="Выберите действие..."
    )