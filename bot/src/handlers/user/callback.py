from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.states.user_states import UserStates
from src.keyboards.user.inline import get_cancel_user_keyboard

router = Router()

@router.callback_query(F.data.startswith("make_proposal:"))
async def make_proposal_callback(callback: types.CallbackQuery, state: FSMContext):
    tender_id = int(callback.data.split(":")[1])
    
    await state.update_data(tender_id=tender_id)
    await state.set_state(UserStates.waiting_for_proposal)
    
    await callback.message.answer(
        "📝 Напишите ваше предложение (или сумму) одним сообщением:",
        reply_markup=get_cancel_user_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_user_action")
async def cancel_user_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()