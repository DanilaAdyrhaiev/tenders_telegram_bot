import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.states.user_states import UserStates
from src.keyboards.user.inline import get_cancel_user_keyboard
from src.utils.lexicon import TEXTS

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("make_proposal:"))
async def make_proposal_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        tender_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга тендера при попытке сделать предложение: {e}")
        return

    await state.update_data(tender_id=tender_id)
    await state.set_state(UserStates.waiting_for_proposal)
    
    logger.info(f"Пользователь {callback.from_user.id} нажал кнопку 'Сделать предложение' для тендера #{tender_id}")
    
    await callback.message.answer(
        TEXTS["messages"]["user"]["ask_proposal_text"],
        reply_markup=get_cancel_user_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_user_action")
async def cancel_user_action(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} отменил текущее действие.")
    await state.clear()
    await callback.message.edit_text(TEXTS["messages"]["common"]["action_cancelled"])
    await callback.answer()