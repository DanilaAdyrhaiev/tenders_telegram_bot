import logging
import html
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
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext, command: CommandObject):
    await state.clear()
    logger.info(f"Пользователь {user.telegram_id} ({user.nickname}) вызвал /start")
    
    if command.args and command.args.startswith("tender_"):
        try:
            tender_id = int(command.args.split("_")[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка парсинга ссылки тендера пользователем {user.telegram_id}: {e}")
            await message.answer(TEXTS["messages"]["user"]["invalid_link"])
            return
            
        tender = await get_tender(tender_id)
        
        if not tender or not tender.is_active:
            logger.info(f"Пользователь {user.telegram_id} попытался открыть неактивный/удаленный тендер #{tender_id}")
            await message.answer(TEXTS["messages"]["user"]["tender_not_found"])
            return

        proposals_text = ""
        if tender.proposals:
            proposals_text = TEXTS["messages"]["user"]["proposals_header"]
            for p in tender.proposals:
                safe_prop_text = html.escape(p.text)
                proposals_text += TEXTS["messages"]["user"]["proposal_item"].format(
                    user_id=p.user_id, text=safe_prop_text
                )
        else:
            proposals_text = TEXTS["messages"]["user"]["proposals_empty"]

        safe_tender_text = html.escape(tender.text)
        text = f"📄 <b>Тендер #{tender.tender_id}</b>\n\n{safe_tender_text}{proposals_text}"
        
        await message.answer(
            text, 
            reply_markup=get_user_tender_keyboard(tender_id), 
            parse_mode="HTML"
        )
    else:
        await message.answer(
            TEXTS["messages"]["user"]["start_default"].format(nickname=html.escape(user.nickname))
        )

@router.message(StateFilter(UserStates.waiting_for_proposal), F.text)
async def process_proposal_text(message: types.Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    tender_id = data.get("tender_id")

    if not tender_id:
        logger.warning(f"Пользователь {user.telegram_id} отправил предложение без tender_id в state")
        await state.clear()
        return

    tender = await get_tender(tender_id)
    if not tender or not tender.is_active:
        logger.info(f"Тендер #{tender_id} закрыт. Предложение от {user.telegram_id} отклонено.")
        await message.answer(TEXTS["messages"]["common"]["tender_closed_error"])
        await state.clear()
        return

    new_proposal = Proposal(user_id=user.telegram_id, text=message.text)
    await add_proposal(tender_id, new_proposal)
    logger.info(f"Пользователь {user.telegram_id} оставил предложение для тендера #{tender_id}")

    await message.answer(
        TEXTS["messages"]["user"]["proposal_sent"], 
        reply_markup=get_user_tender_keyboard(tender_id)
    )
    await state.clear()

    unique_users = set(p.user_id for p in tender.proposals)
    unique_users.discard(user.telegram_id) 

    safe_prop_text = html.escape(message.text)

    for uid in unique_users:
        try:
            notify_text = TEXTS["notifications"]["new_proposal"].format(
                tender_id=tender_id, user_id=user.telegram_id, text=safe_prop_text
            )
            await bot.send_message(
                chat_id=uid,
                text=notify_text,
                reply_markup=get_user_tender_keyboard(tender_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление о ставке участнику {uid}: {e}")