from aiogram.types import Message
from aiogram import Router, F, types
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.client.bot import Bot
from src.models.user import User
from src.models.tender import Proposal
from src.utils.db import get_tender, add_proposal
from src.states.user_states import UserStates
from src.keyboards.user.inline import get_user_tender_keyboard
import html

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext, command: CommandObject):
    await state.clear()
    
    if command.args and command.args.startswith("tender_"):
        try:
            tender_id = int(command.args.split("_")[1])
        except (IndexError, ValueError):
            await message.answer("❌ Неверная ссылка на тендер.")
            return
            
        tender = await get_tender(tender_id)
        
        if not tender or not tender.is_active:
            await message.answer("❌ Этот тендер не найден или уже закрыт.")
            return

        proposals_text = ""
        if tender.proposals:
            proposals_text = "\n\n💬 <b>Текущие предложения других участников:</b>\n"
            for p in tender.proposals:
                safe_prop_text = html.escape(p.text)
                proposals_text += f"👤 Участник #{p.user_id}: {safe_prop_text}\n"
        else:
            proposals_text = "\n\n📭 Пока нет предложений. Будьте первым!"

        safe_tender_text = html.escape(tender.text)
        text = f"📄 <b>Тендер #{tender.tender_id}</b>\n\n{safe_tender_text}{proposals_text}"
        
        await message.answer(
            text, 
            reply_markup=get_user_tender_keyboard(tender_id), 
            parse_mode="HTML"
        )
        
    else:
        await message.answer(f"Добрый день, {html.escape(user.nickname)}!\nЯ бот для участия в тендерах.")

@router.message(StateFilter(UserStates.waiting_for_proposal), F.text)
async def process_proposal_text(message: types.Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    tender_id = data.get("tender_id")

    if not tender_id:
        await state.clear()
        return

    tender = await get_tender(tender_id)
    if not tender or not tender.is_active:
        await message.answer("❌ Тендер уже закрыт.")
        await state.clear()
        return

    # 1. Сохраняем предложение юзера
    new_proposal = Proposal(user_id=user.telegram_id, text=message.text)
    await add_proposal(tender_id, new_proposal)

    await message.answer(
        "✅ Ваше предложение успешно отправлено!", 
        reply_markup=get_user_tender_keyboard(tender_id)
    )
    await state.clear()

    # 2. РАССЫЛКА КОНКУРЕНТАМ (уведомляем тех, кто уже сделал ставку)
    # Собираем уникальные ID всех, кто оставлял заявки
    unique_users = set(p.user_id for p in tender.proposals)
    unique_users.discard(user.telegram_id) 

    for uid in unique_users:
        try:
            await bot.send_message(
                chat_id=uid,
                text=f"🔔Новое предложение в тендере #{tender_id}!\n\n👤 Участник #{user.telegram_id} предложил:\n{message.text}\n\nВы можете перебить ставку!",
                reply_markup=get_user_tender_keyboard(tender_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление {uid}: {e}")