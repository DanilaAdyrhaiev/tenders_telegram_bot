from pydantic import BaseModel, Field
from typing import List, Optional
from .user import User

class Proposal(BaseModel):
    user_id: int                  # ID пользователя в Telegram
    text: str                     # Текст самого предложения / сумма

class Tender(BaseModel):
    tender_id: int               # Уникальный ID (например, "1", "2" или случайный хэш)
    text: str                     # Текст описания тендера (который пишет админ)
    is_active: bool = True        # Флаг активности (True - открыт, False - закрыт)
    proposals: Optional[List[Proposal]] = [] # Список всех предложений по этому тендеру
    winner: Optional[User] = None
    channel_message_id: Optional[int] = None

    def redis_key(self) -> str:
        return f"tender:{self.tender_id}"