import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

def get_user_tender_keyboard(tender_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["user"]["make_proposal"], callback_data=f"make_proposal:{tender_id}")
    return builder.as_markup()

def get_cancel_user_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["common"]["cancel"], callback_data="cancel_user_action")
    return builder.as_markup()