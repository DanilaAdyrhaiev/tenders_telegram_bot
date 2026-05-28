from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from typing import Optional, List
from aiogram.fsm.context import FSMContext
from aiogram.client.bot import Bot
import html

from src.models.user import User
from src.models.tender import Tender
from src.utils.db import get_user, save_user, get_users, get_tenders_count, save_tender, get_tender
from src.utils.db import get_active_tenders, get_all_tenders
from src.keyboards.admin.inline import get_confirm_winner_keyboard, get_proposal_view_keyboard, get_proposals_list_keyboard, get_user_manage_keyboard, get_users_list_keyboard
from src.keyboards.admin.inline import get_cancel_keyboard, get_participate_keyboard
from src.keyboards.admin.inline import get_tenders_menu, get_tenders_list_keyboard
from src.keyboards.admin.inline import get_tender_manage_keyboard
from src.utils.filters import TargetUserFilter, isAdminFilter
from src.states.admin_states import CreateTender
from src.utils.config import settings
from src.states.admin_states import EditTender



router = Router()

def get_user_profile_text(target_user: User, is_updated: bool = False) -> str:
    status = "❌ Заблокирован" if target_user.is_banned else "✅ Активен"
    is_admin_str = "Да" if target_user.is_admin else "Нет"
    
    title = "👤 Профиль участника (Статус обновлен!)" if is_updated else "👤 Профиль участника"

    return (
        f"{title}\n\n"
        f"• Никнейм: {target_user.nickname}\n"
        f"• Telegram ID: `{target_user.telegram_id}`\n"
        f"• Юзернейм: @{target_user.username or 'отсутствует'}\n"
        f"• Администратор: {is_admin_str}\n"
        f"• Статус: {status}"
    )


#ЮЗЕРЫ
@router.callback_query(F.data.startswith("view_user:"), isAdminFilter(), TargetUserFilter())
async def process_view_user(callback: types.CallbackQuery, target_user: User):
    await callback.message.edit_text(
        text=get_user_profile_text(target_user),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_banned),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_ban:"), isAdminFilter(), TargetUserFilter())
async def process_toggle_ban(callback: types.CallbackQuery, target_user: User):
    target_user.is_banned = not target_user.is_banned
    await save_user(target_user)

    alert_msg = "Пользователь заблокирован!" if target_user.is_banned else "Пользователь разблокирован!"
    await callback.answer(alert_msg)
    
    await callback.message.edit_text(
        text=get_user_profile_text(target_user, is_updated=True),
        reply_markup=get_user_manage_keyboard(target_user.telegram_id, target_user.is_banned),
        parse_mode="Markdown"
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
    if u.telegram_id != callback.from_user.id and not u.is_admin and not u.is_root]
    
    await callback.message.edit_text(
        "👥 Список участников проекта:\nВыберите пользователя для управления:",
        reply_markup=get_users_list_keyboard(filtered_users),
        parse_mode="Markdown"
    )
    await callback.answer()


#ТЕНДЕР
@router.callback_query(F.data == "get_active_tenders", isAdminFilter())
async def show_active_tenders(callback: types.CallbackQuery):
    tenders = await get_active_tenders()
    
    if not tenders:
        await callback.message.edit_text("📭 Активных тендеров нет.", reply_markup=get_tenders_menu())
        return
    
    # Передаем page=1 и list_type="active"
    await callback.message.edit_text(
        "🟢 Список активных тендеров:",
        reply_markup=get_tenders_list_keyboard(tenders, page=1, list_type="active")
    )

@router.callback_query(F.data == "get_all_tenders", isAdminFilter())
async def show_all_tenders(callback: types.CallbackQuery):
    tenders = await get_all_tenders()
    
    if not tenders:
        await callback.message.edit_text("📭 В базе пока нет тендеров.", reply_markup=get_tenders_menu())
        return
    
    await callback.message.edit_text(
        "🗂 Список всех тендеров:",
        reply_markup=get_tenders_list_keyboard(tenders, page=1, list_type="all")
    )

@router.callback_query(F.data.startswith("page:"), isAdminFilter())
async def process_pagination(callback: types.CallbackQuery):
    _, list_type, page_str = callback.data.split(":")
    page = int(page_str)
    
    if list_type == "active":
        tenders = await get_active_tenders()
        text = "🟢 Список активных тендеров:"
    else:
        tenders = await get_all_tenders()
        text = "🗂 Список всех тендеров:"
        
    await callback.message.edit_reply_markup(
        text=text,
        reply_markup=get_tenders_list_keyboard(tenders, page=page, list_type=list_type)
    )

@router.callback_query(F.data == "ignore", isAdminFilter())
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("view_tender:"), isAdminFilter())
async def view_specific_tender(callback: types.CallbackQuery):
    tender_id = int(callback.data.split(":")[1])
    tender = await get_tender(tender_id)
    
    if not tender:
        await callback.answer("❌ Тендер не найден!", show_alert=True)
        return
        
    status = "🟢 Активен" if tender.is_active else "🔴 Закрыт"
    proposals_count = len(tender.proposals) if tender.proposals else 0
    if tender.winner:
        safe_nickname = html.escape(tender.winner.nickname)
        winner_text = f"\n<b>🏆 Победитель:</b> {safe_nickname}"
    else:
        winner_text = ""

    safe_tender_text = html.escape(tender.text)

    text = (
        f"📄 <b>Тендер #{tender.tender_id}</b>\n\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Откликов:</b> {proposals_count}{winner_text}\n\n"
        f"<b>Описание:</b>\n{safe_tender_text}" # <--- Просто переменная
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
        f"📝 Введите новый текст для тендера #{tender_id}:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_proposals:"), isAdminFilter())
async def view_tender_proposals(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    page = int(parts[2])
    
    tender = await get_tender(tender_id)
    if not tender or not tender.proposals:
        await callback.answer("📭 Пока нет предложений.", show_alert=True)
        return
        
    await callback.message.edit_text(
        f"💬Предложения по тендеру #{tender_id}nВыберите участника для просмотра:",
        reply_markup=get_proposals_list_keyboard(tender_id, tender.proposals, page=page),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_tenders_menu", isAdminFilter())
async def process_back_to_tenders_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📢Управление тендерами**\n\nВыберите нужное действие в меню ниже:",
        reply_markup=get_tenders_menu(),
        parse_mode="Markdown"
    )
    # Не забываем ответить телеграму, чтобы "часики" на кнопке пропали
    await callback.answer()

@router.callback_query(F.data.startswith("view_single_prop:"), isAdminFilter())
async def view_single_proposal(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    tender = await get_tender(tender_id)
    user = await get_user(user_id)
    
    proposal = next((p for p in tender.proposals if p.user_id == user_id), None)
    
    if not proposal or not user:
        await callback.answer("❌ Ошибка загрузки предложения.", show_alert=True)
        return
        
    text = (
        f"👤Участник:** {user.nickname} (@{user.username})\n\n"
        f"**Текст предложения:n{proposal.text}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_proposal_view_keyboard(tender_id, user_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("ask_winner:"), isAdminFilter())
async def ask_confirm_winner(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    await callback.message.edit_text(
        "❓Вы уверены**, что хотите выбрать этого участника победителем и закрыть тендер?",
        reply_markup=get_confirm_winner_keyboard(tender_id, user_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_winner:"), isAdminFilter())
async def confirm_tender_winner(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    tender_id = int(parts[1])
    user_id = int(parts[2])
    
    tender = await get_tender(tender_id)
    winner_user = await get_user(user_id)
    
    if not tender.is_active:
        await callback.answer("❌ Тендер уже закрыт!", show_alert=True)
        return
        
    # Сохраняем в БД через Pydantic-модель
    tender.is_active = False
    tender.winner = winner_user
    await save_tender(tender)
    
    # Удаляем сообщение в канале
    if tender.channel_message_id:
        try:
            await bot.delete_message(chat_id=settings.CHANNEL_ID, message_id=tender.channel_message_id)
        except Exception as e:
            print(f"Не удалось удалить пост тендера #{tender_id} из канала: {e}")
    
    # Обновляем админу сообщение
    await callback.message.edit_text(
        f"✅Тендер #{tender_id} закрыт!nПобедитель: {winner_user.nickname}\nПост удален из канала.\n\nРассылка уведомлений запущена.",
        reply_markup=get_tender_manage_keyboard(tender_id, len(tender.proposals), False),
        parse_mode="Markdown"
    )

    # ТУТ БУДЕТ ЛОГИКА РАССЫЛКИ

    if tender.proposals:
        # Собираем уникальные ID всех, кто оставлял предложения (чтобы не отправить 2 раза одному человеку)
        unique_participants = set(p.user_id for p in tender.proposals)
        
        for participant_id in unique_participants:
            try:
                # Если ID участника совпадает с ID победителя
                if participant_id == winner_user.telegram_id:
                    text = (
                        f"🎉 <b>Поздравляем!</b>\n\n"
                        f"Ваше предложение по тендеру <b>#{tender_id}</b> было выбрано победным! "
                        f"В ближайшее время администратор свяжется с вами для обсуждения деталей."
                    )
                # Для всех остальных (проигравших)
                else:
                    text = (
                        f"🔔 <b>Тендер #{tender_id} завершен!</b>\n\n"
                        f"К сожалению, в этот раз заказчик выбрал другого исполнителя. "
                        f"Не расстраивайтесь, впереди еще много интересных проектов!"
                    )
                
                # Отправляем сообщение
                await bot.send_message(
                    chat_id=participant_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                # Если юзер заблокировал бота, скрипт не должен упасть — просто выводим ошибку в консоль и идем дальше
                print(f"Ошибка при отправке уведомления юзеру {participant_id}: {e}")

@router.callback_query(F.data == "create_tender")
async def admin_publishing_tender(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateTender.waiting_for_text)
    await callback.message.edit_text(
        "📝 Введите текст для тендера:", 
        reply_markup=get_cancel_keyboard()
    )


@router.callback_query(F.data == "confirm_tender", CreateTender.waiting_for_confirmation, isAdminFilter())
async def confirm_tender_publication( callback: types.CallbackQuery, state: FSMContext, 
    bot: Bot, user: User):
    user_data = await state.get_data()
    tender_text = user_data.get("tender_text")
    try:
        new_tender_id = await get_tenders_count() + 1
        bot_info = await bot.get_me()
        channel_post = f"💼 Тендер №{new_tender_id}\n\n{tender_text}"
        
        
        msg = await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=channel_post,
            reply_markup=get_participate_keyboard(new_tender_id, bot_info.username)
        )
        
        new_tender = Tender(
            tender_id=new_tender_id,
            text=tender_text,
            is_active=True,
            proposals=[],
            channel_message_id=msg.message_id
        )
        await save_tender(new_tender)
        await callback.message.edit_text(f"✅ Тендер №{new_tender_id} успешно опубликован в канале!")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка публикации в канал: {e}")
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "edit_tender", CreateTender.waiting_for_confirmation, isAdminFilter())
async def edit_tender_text(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateTender.waiting_for_text)
    await callback.message.edit_text(
        "📝 Хорошо, введите новый измененный текст для тендера:", 
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_tender", StateFilter(CreateTender), isAdminFilter())
async def cancel_tender_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Публикация тендера отменена.")
    await callback.answer()

@router.callback_query(F.data == "cancel_tender_edit", StateFilter(EditTender), isAdminFilter())
async def cancel_tender_edit(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tender_id = data.get("edit_tender_id")
    
    await state.clear()
    
    if not tender_id:
        await callback.message.edit_text("❌ Действие отменено.")
        return

    # Получаем актуальные данные тендера из базы
    tender = await get_tender(tender_id)
    if not tender:
         await callback.message.edit_text("❌ Действие отменено. Тендер не найден.")
         return
         
    status = "🟢 Активен" if tender.is_active else "🔴 Закрыт"
    proposals_count = len(tender.proposals) if tender.proposals else 0
    winner_text = f"\n**🏆 Победитель:** {tender.winner.nickname}" if tender.winner else ""
    
    text = (
        f"📄Тендер #{tender.tender_id}**\n\n"
        f"**Статус:** {status}\n"
        f"**Откликов:** {proposals_count}{winner_text}\n\n"
        f"**Описание:**\n{tender.text}"
    )
    
    # Возвращаем админа в меню конкретного тендера
    await callback.message.edit_text(
        text, 
        reply_markup=get_tender_manage_keyboard(tender.tender_id, proposals_count, tender.is_active),
        parse_mode="Markdown"
    )