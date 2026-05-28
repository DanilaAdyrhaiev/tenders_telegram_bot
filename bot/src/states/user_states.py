from aiogram.fsm.state import StatesGroup, State

class UserStates(StatesGroup):
    waiting_for_proposal = State()
    