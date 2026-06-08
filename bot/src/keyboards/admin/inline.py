import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
import math

from src.models.user import User
from src.models.tender import Tender, Proposal
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)

def get_users_list_keyboard(users: Optional[List[User]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if users:
        for user in users:
            if user.is_admin or user.is_root:
                continue
            display_name = f"{user.nickname} (@{user.username})" if user.username else user.username or user.nickname
            if user.is_banned:
                display_name += " 🚫"
            builder.button(text=display_name, callback_data=f"view_user:{user.telegram_id}")
        
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text=TEXTS["buttons"]["common"]["back"], callback_data="back_to_menu")
    )
    return builder.as_markup()

def get_user_manage_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ban_text = TEXTS["buttons"]["admin"]["unban"] if is_banned else TEXTS["buttons"]["admin"]["ban"]
    
    builder.button(text=ban_text, callback_data=f"toggle_ban:{user_id}")
    builder.button(text=TEXTS["buttons"]["admin"]["back_to_users"], callback_data="back_to_users_list")
    
    builder.adjust(1)
    return builder.as_markup()

def get_tenders_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["admin"]["active_tenders"], callback_data="get_active_tenders")
    builder.button(text=TEXTS["buttons"]["admin"]["all_tenders"], callback_data="get_all_tenders")
    builder.button(text=TEXTS["buttons"]["admin"]["create_tender"], callback_data="create_tender")
    builder.adjust(1) 
    return builder.as_markup()

def get_tenders_list_keyboard(tenders: List[Tender], page: int = 1, per_page: int = 5, list_type: str = "all") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = math.ceil(len(tenders) / per_page)
    if total_pages == 0:
        total_pages = 1
        
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    tenders_on_page = tenders[start_idx:end_idx]
    
    for tender in tenders_on_page:
        status_emoji = "🟢" if tender.is_active else "🔴"
        short_text = tender.text[:25] + "..." if len(tender.text) > 25 else tender.text
        btn_text = f"{status_emoji} #{tender.tender_id} | {short_text}"
        builder.button(text=btn_text, callback_data=f"view_tender:{tender.tender_id}")
    
    builder.adjust(1) 
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page:{list_type}:{page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page:{list_type}:{page + 1}"))
        
    builder.row(*nav_buttons)
    builder.row(
        InlineKeyboardButton(text=TEXTS["buttons"]["common"]["back_to_menu"], callback_data="back_to_tenders_menu")
    )
    return builder.as_markup()

def get_tender_manage_keyboard(tender_id: int, proposals_count: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_active:
        builder.button(text=TEXTS["buttons"]["admin"]["edit_text"], callback_data=f"edit_tender_text:{tender_id}")
        
    # Форматируем динамическое число откликов в строке кнопки
    proposals_btn_text = TEXTS["buttons"]["admin"]["proposals_count"].format(count=proposals_count)
    builder.button(text=proposals_btn_text, callback_data=f"view_proposals:{tender_id}:1")
    
    builder.button(text=TEXTS["buttons"]["common"]["back"], callback_data="get_all_tenders")
    builder.adjust(1)
    return builder.as_markup()

def get_proposals_list_keyboard(tender_id: int, proposals: List[Proposal], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = math.ceil(len(proposals) / per_page) or 1
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    proposals_on_page = proposals[start_idx:end_idx]
    
    for prop in proposals_on_page:
        short_text = prop.text[:15] + "..." if len(prop.text) > 15 else prop.text
        builder.button(text=f"👤 {prop.user_id} | {short_text}", callback_data=f"view_single_prop:{tender_id}:{prop.user_id}")
    
    builder.adjust(1)
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"view_proposals:{tender_id}:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"view_proposals:{tender_id}:{page + 1}"))
        
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text=TEXTS["buttons"]["admin"]["back_to_tender"], callback_data=f"view_tender:{tender_id}"))
    return builder.as_markup()

def get_proposal_view_keyboard(tender_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["admin"]["choose_winner"], callback_data=f"ask_winner:{tender_id}:{user_id}")
    builder.button(text=TEXTS["buttons"]["admin"]["back_to_tender"], callback_data=f"view_proposals:{tender_id}:1")
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_winner_keyboard(tender_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["admin"]["confirm_winner"], callback_data=f"confirm_winner:{tender_id}:{user_id}")
    builder.button(text=TEXTS["buttons"]["admin"]["cancel_winner"], callback_data=f"view_single_prop:{tender_id}:{user_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_tender_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["admin"]["edit_text"], callback_data="edit_tender")
    builder.button(text=TEXTS["buttons"]["admin"]["confirm"], callback_data="confirm_tender")
    builder.button(text=TEXTS["buttons"]["common"]["cancel"], callback_data="cancel_tender")
    builder.adjust(1, 2) 
    return builder.as_markup()

def get_participate_keyboard(tender_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    link = f"https://t.me/{bot_username}?start=tender_{tender_id}"
    builder.button(text=TEXTS["buttons"]["user"]["participate"], url=link)
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=TEXTS["buttons"]["common"]["cancel"], callback_data="cancel_tender_edit")
    return builder.as_markup()