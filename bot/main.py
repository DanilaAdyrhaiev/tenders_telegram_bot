import asyncio
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from src.utils.config import settings
from src.handlers import router as main_router
from src.utils.middleware import UserMiddleware

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

error_handler = RotatingFileHandler(
    "logs/bot_errors.log", 
    maxBytes=5*1024*1024, # 5 MB
    backupCount=3, 
    encoding="utf-8"
)

error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
error_handler.setFormatter(error_formatter)
logging.getLogger("").addHandler(error_handler)

logger = logging.getLogger(__name__)


async def main():
    session = AiohttpSession()
    bot = Bot(
        token=settings.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode='HTML')
    )

    dp = Dispatcher()
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())
    dp.include_router(main_router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        logging.info("Бот успешно запущен")
    except ValueError as e:
        logger.error("ValueError occured %s: ", e)
    except KeyError as e:
        logger.error("KeyError occured %s: ", e)
    except Exception as e:
        logging.error("Бот упал с ошибкой: %s", e, exc_info=True)
    finally:
        logging.info("Запуск экстренного сохранения данных...")
        
        await bot.session.close()
        logging.info("Все соединения закрыты. Бот полностью остановлен.")

if __name__ == "__main__":
    asyncio.run(main())