import logging
import html
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.client.bot import Bot

from src.models.user import User
from src.models.tender import Tender
from src.utils.db import get_user, save_user, get_users, get_tenders_count, save_tender, get_tender
from src.utils.db import get_active_tenders, get_all_tenders
from src.keyboards.admin.inline import (
    get_confirm_winner_keyboard, get_proposal_view_keyboard, get_proposals_list_keyboard, 
    get_user_manage_keyboard, get_users_list_keyboard, get_cancel_keyboard, 
    get_participate_keyboard, get_tenders_menu, get_tenders_list_keyboard, 
    get_tender_manage_keyboard
)
from src.utils.filters import TargetUserFilter, isAdminFilter
from src.states.admin_states import CreateTender, EditTender
from src.utils.config import settings
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)
router = Router()

def get_user_profile_text(target_user: User, is_updated: bool = False) -> str:
    status = TEXTS["messages"]["profile"]["status_banned"] if target_user.is_banned else TEXTS["messages"]["profile"]["status_active"]
    is_admin_str = TEXTS["messages"]["profile"]["yes"] if target_user.is_admin else TEXTS["messages"]["profile"]["no"]
    title = TEXTS["messages"]["profile"]["title_updated"] if is_updated else TEXTS["messages"]["profile"]["title_normal"]
    
    return TEXTS["messages"]["profile"]["body"].format(
        title=title,
        nickname=html.escape(target_user.nickname),
        telegram_id=target_user.telegram_id,
        username=html.escape(target_user.username or 'отсутствует'),
        is_admin=is_admin_str,
        status=status
    )

@router.callback_query(F.data.startswith("view_user:"), isAdminFilter(), TargetUserFilter())
async def process_view_user(callback: types.CallbackQuery, target_user: User):
    await callback.message.edit_text(
        text=get_user_profile_text(target_user),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_banned),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_ban:"), isAdminFilter(), TargetUserFilter())
async def process_toggle_ban(callback: types.CallbackQuery, target_user: User):
    target_user.is_banned = not target_user.is_banned
    await save_user(target_user)
    alert_msg = TEXTS["messages"]["admin"]["user_banned_alert"] if target_user.is_banned else TEXTS["messages"]["admin"]["user_unbanned_alert"]
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_banned),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_menu", isAdminFilter())
async def process_close_inline(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "back_to_users_list", isAdminFilter())
async def process_back_to_users(callback: types.CallbackQuery):
    all_users = await get_users()
    filtered_users = [
        u for u in all_users 
        if u.telegram_id != callback.from_user.id and not u.is_admin and not u.is_root
    ]
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["users_list"],
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "get_active_tenders", isAdminFilter())
async def show_active_tenders(callback: types.CallbackQuery):
    tenders = await get_active_tenders()
    if not tenders:
        await callback.message.edit_text(
            TEXTS["messages"]["admin"]["tenders_active_empty"], 
            reply_markup=get_tenders_menu(), parse_mode="HTML"
        )
        return
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["tenders_active_list"],
        reply_markup=get_tenders_list_keyboard(tenders, page=1, list_type="active"), parse_mode="HTML"
    )

@router.callback_query(F.data == "get_all_tenders", isAdminFilter())
async def show_all_tenders(callback: types.CallbackQuery):
    tenders = await get_all_tenders()
    if not tenders:
        await callback.message.edit_text(
            TEXTS["messages"]["admin"]["tenders_all_empty"], 
            reply_markup=get_tenders_menu(), parse_mode="HTML"
        )
        return
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["tenders_all_list"],
        reply_markup=get_tenders_list_keyboard(tenders, page=1, list_type="all"), parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("page:"), isAdminFilter())
async def process_pagination(callback: types.CallbackQuery):
    try:
        _, list_type, page_str = callback.data.split(":")
        page = int(page_str)
    except Exception:
        return
    if list_type == "active":
        tenders = await get_active_tenders()
        text = TEXTS["messages"]["admin"]["tenders_active_list"]
    else:
        tenders = await get_all_tenders()
        text = TEXTS["messages"]["admin"]["tenders_all_list"]
        
    await callback.message.edit_reply_markup(
        text=text, reply_markup=get_tenders_list_keyboard(tenders, page=page, list_type=list_type)
    )

@router.callback_query(F.data == "ignore", isAdminFilter())
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("view_tender:"), isAdminFilter())
async def view_specific_tender(callback: types.CallbackQuery):
    try:
        tender_id = int(callback.data.split(":")[1])
    except Exception:
        return
    tender = await get_tender(tender_id)
    if not tender:
        await callback.answer(TEXTS["messages"]["admin"]["tender_not_found"], show_alert=True)
        return
        
    status = TEXTS["messages"]["admin"]["status_active"] if tender.is_active else TEXTS["messages"]["admin"]["status_closed"]
    proposals_count = len(tender.proposals) if tender.proposals else 0
    
    if tender.winner:
        winner_text = TEXTS["messages"]["admin"]["winner_text_html"].format(nickname=html.escape(tender.winner.nickname))
    else:
        winner_text = ""

    text = TEXTS["messages"]["admin"]["tender_card_html"].format(
        tender_id=tender.tender_id,
        status=status,
        proposals_count=proposals_count,
        winner_text=winner_text,
        text=tender.text # текст уже эскейпится при сохранении
    )
    
    await callback.message.edit_text(
        text, 
        reply_markup=get_tender_manage_keyboard(tender.tender_id, proposals_count, tender.is_active),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("edit_tender_text:"), isAdminFilter())
async def process_edit_existing_tender(callback: types.CallbackQuery, state: FSMContext):
    tender_id = int(callback.data.split(":")[1])
    await state.update_data(edit_tender_id=tender_id)
    await state.set_state(EditTender.waiting_for_new_text)
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["enter_new_text"].format(tender_id=tender_id),
        reply_markup=get_cancel_keyboard(), parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_tenders_menu", isAdminFilter())
async def process_back_to_tenders_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["tenders_menu"],
        reply_markup=get_tenders_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_proposals:"), isAdminFilter())
async def view_tender_proposals(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    page = int(parts[2])
    tender = await get_tender(tender_id)
    if not tender or not tender.proposals:
        await callback.answer(TEXTS["messages"]["admin"]["proposals_empty"], show_alert=True)
        return
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["proposals_list"].format(tender_id=tender_id),
        reply_markup=get_proposals_list_keyboard(tender_id, tender.proposals, page=page),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("view_single_prop:"), isAdminFilter())
async def view_single_proposal(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    tender = await get_tender(tender_id)
    user = await get_user(user_id)
    proposal = next((p for p in tender.proposals if p.user_id == user_id), None)
    
    if not proposal or not user:
        await callback.answer(TEXTS["messages"]["admin"]["proposal_load_error"], show_alert=True)
        return
        
    text = TEXTS["messages"]["admin"]["proposal_view"].format(
        nickname=html.escape(user.nickname),
        username=html.escape(user.username or "отсутствует"),
        text=html.escape(proposal.text)
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_proposal_view_keyboard(tender_id, user_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("ask_winner:"), isAdminFilter())
async def ask_confirm_winner(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["ask_winner"],
        reply_markup=get_confirm_winner_keyboard(tender_id, user_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("confirm_winner:"), isAdminFilter())
async def confirm_tender_winner(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    tender = await get_tender(tender_id)
    winner_user = await get_user(user_id)
    
    if not tender.is_active:
        await callback.answer(TEXTS["messages"]["admin"]["tender_closed_error"], show_alert=True)
        return
        
    tender.is_active = False
    tender.winner = winner_user
    await save_tender(tender)

    if tender.channel_message_id:
        try:
            await bot.delete_message(chat_id=settings.CHANNEL_ID, message_id=tender.channel_message_id)
        except Exception:
            pass
    
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["tender_successfully_closed"].format(
            tender_id=tender_id, nickname=html.escape(winner_user.nickname)
        ),
        reply_markup=get_tender_manage_keyboard(tender_id, len(tender.proposals), False),
        parse_mode="HTML"
    )

    if tender.proposals:
        unique_participants = set(p.user_id for p in tender.proposals)
        for participant_id in unique_participants:
            try:
                if participant_id == winner_user.telegram_id:
                    text = TEXTS["notifications"]["winner_congrats"].format(tender_id=tender_id)
                else:
                    text = TEXTS["notifications"]["loser_notify"].format(tender_id=tender_id)
                
                await bot.send_message(chat_id=participant_id, text=text, parse_mode="HTML")
            except Exception:
                pass

@router.callback_query(F.data == "create_tender")
async def admin_publishing_tender(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateTender.waiting_for_text)
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["enter_tender_text"], 
        reply_markup=get_cancel_keyboard(), parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm_tender", CreateTender.waiting_for_confirmation, isAdminFilter())
async def confirm_tender_publication(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    tender_text = user_data.get("tender_text") # уже эскейплен в message.py
    try:
        new_tender_id = await get_tenders_count() + 1
        bot_info = await bot.get_me()
        
        channel_post = TEXTS["messages"]["user"]["channel_post"].format(
            tender_id=new_tender_id, text=tender_text
        )
        msg = await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=channel_post,
            reply_markup=get_participate_keyboard(new_tender_id, bot_info.username),
            parse_mode="HTML"
        )
        
        new_tender = Tender(
            tender_id=new_tender_id, text=tender_text, is_active=True,
            proposals=[], channel_message_id=msg.message_id
        )
        await save_tender(new_tender)
        await callback.message.edit_text(
            TEXTS["messages"]["admin"]["publish_success"].format(tender_id=new_tender_id), parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            TEXTS["messages"]["admin"]["publish_error"].format(error=html.escape(str(e))), parse_mode="HTML"
        )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "edit_tender", CreateTender.waiting_for_confirmation, isAdminFilter())
async def edit_tender_text(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateTender.waiting_for_text)
    await callback.message.edit_text(
        TEXTS["messages"]["admin"]["enter_tender_text"], 
        reply_markup=get_cancel_keyboard(), parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_tender", StateFilter(CreateTender), isAdminFilter())
async def cancel_tender_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(TEXTS["messages"]["admin"]["publish_cancelled"], parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "cancel_tender_edit", StateFilter(EditTender), isAdminFilter())
async def cancel_tender_edit(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tender_id = data.get("edit_tender_id")
    await state.clear()
    if not tender_id:
        await callback.message.edit_text(TEXTS["messages"]["common"]["action_cancelled"], parse_mode="HTML")
        return
    tender = await get_tender(tender_id)
    if not tender:
         await callback.message.edit_text(f"{TEXTS['messages']['common']['action_cancelled']}", parse_mode="HTML")
         return
         
    status = TEXTS["messages"]["admin"]["status_active"] if tender.is_active else TEXTS["messages"]["admin"]["status_closed"]
    proposals_count = len(tender.proposals) if tender.proposals else 0
    winner_text = TEXTS["messages"]["admin"]["winner_text_html"].format(nickname=html.escape(tender.winner.nickname)) if tender.winner else ""
    
    text = TEXTS["messages"]["admin"]["tender_card_html"].format(
        tender_id=tender.tender_id, status=status, proposals_count=proposals_count,
        winner_text=winner_text, text=tender.text
    )
    await callback.message.edit_text(
        text, reply_markup=get_tender_manage_keyboard(tender.tender_id, proposals_count, tender.is_active), parse_mode="HTML"
    )