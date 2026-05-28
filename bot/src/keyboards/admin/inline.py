from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
import math

from src.models.user import User
from src.models.tender import Tender, Proposal

def get_users_list_keyboard(users: Optional[List[User]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for user in users:
        if user.is_admin or user.is_root:
            continue
        else:
            display_name = f"{user.nickname} (@{user.username})" if user.username else user.username or user.nickname
            if user.is_banned:
                display_name += " 🚫" # Пометка в списке, если забанен
            builder.button(text=display_name, callback_data=f"iew_user:{user.telegram_id}")
        
    builder.adjust(1)
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()

def get_user_manage_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ban_text = "🟢 Разбанить" if is_banned else "🚫 Забанить"
    
    builder.button(text=ban_text, callback_data=f"toggle_ban:{user_id}")
    builder.button(text="⬅️ К списку участников", callback_data="back_to_users_list")
    
    builder.adjust(1)
    return builder.as_markup()

#Тендеры
def get_tenders_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Активные тендеры", callback_data="get_active_tenders")
    builder.button(text="🗂️ Все тендеры", callback_data="get_all_tenders")
    builder.button(text="📝 Создать тендер", callback_data="create_tender")
    builder.adjust(1) 
    return builder.as_markup()

    #Список тендера
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
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_tenders_menu")
    )
    
    return builder.as_markup()

def get_tender_manage_keyboard(tender_id: int, proposals_count: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if is_active:
        builder.button(text="✏️ Изменить текст", callback_data=f"edit_tender_text:{tender_id}")
        
    # Кнопка с предложениями (сразу показываем их количество)
    builder.button(text=f"💬 Предложения ({proposals_count})", callback_data=f"view_proposals:{tender_id}:1")
    
    builder.button(text="⬅️ Назад", callback_data="get_all_tenders")
    builder.adjust(1)
    return builder.as_markup()


def get_proposals_list_keyboard(tender_id: int, proposals: List[Proposal], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    import math
    total_pages = math.ceil(len(proposals) / per_page) or 1
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    proposals_on_page = proposals[start_idx:end_idx]
    
    for prop in proposals_on_page:
        # Выводим ID юзера и кусочек текста для понятности
        short_text = prop.text[:15] + "..." if len(prop.text) > 15 else prop.text
        builder.button(text=f"👤 {prop.user_id} | {short_text}", callback_data=f"view_single_prop:{tender_id}:{prop.user_id}")
    
    builder.adjust(1)
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"view_proposals:{tender_id}:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"view_proposals:{tender_id}:{page + 1}"))
        
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="⬅️ Назад к тендеру", callback_data=f"view_tender:{tender_id}"))
    
    return builder.as_markup()

def get_proposal_view_keyboard(tender_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏆 Выбрать победителем", callback_data=f"ask_winner:{tender_id}:{user_id}")
    builder.button(text="⬅️ Назад к списку", callback_data=f"view_proposals:{tender_id}:1")
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_winner_keyboard(tender_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, закрыть тендер", callback_data=f"confirm_winner:{tender_id}:{user_id}")
    builder.button(text="❌ Нет, отмена", callback_data=f"view_single_prop:{tender_id}:{user_id}")
    builder.adjust(1)
    return builder.as_markup()

    #Создание тендера
def get_confirm_tender_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить текст", callback_data="edit_tender")
    builder.button(text="✅ Подтвердить", callback_data="confirm_tender")
    builder.button(text="❌ Отмена", callback_data="cancel_tender")
    builder.adjust(1,2) 
    return builder.as_markup()

def get_participate_keyboard(tender_id: int, bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    link = f"https://t.me/{bot_username}?start=tender_{tender_id}"
    builder.button(text="🙋 Участвовать", url=link)
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_tender_edit")
    return builder.as_markup()
