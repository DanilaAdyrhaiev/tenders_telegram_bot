from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    CHANNEL_ID: int
    ROOT_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()