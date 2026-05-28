from aiogram.fsm.state import StatesGroup, State

class CreateTender(StatesGroup):
    waiting_for_text = State()         
    waiting_for_confirmation = State()

class EditTender(StatesGroup):
    waiting_for_new_text = State()