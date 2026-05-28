from dataclasses import dataclass
from pydantic import BaseModel, Field

class User(BaseModel):
    telegram_id: int = Field(..., description="Уникальный ID пользователя в Telegram")
    username: str | None = Field(None, description="Username пользователя (без @)")
    nickname: str = Field(..., description="Имя/Никнейм пользователя")
    is_admin: bool = Field(default=False, description="Флаг администратора")
    is_root: bool = Field(default=False, description="Флаг суперпользователя")
    is_banned: bool = False

    def redis_key(self) -> str:
        return f"user:{self.telegram_id}"

