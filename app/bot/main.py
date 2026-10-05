from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.bot.menu_handlers import router as menu_router
from app.config import get_settings
from app.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    await init_db()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(menu_router)
    dispatcher.include_router(router)

    logger.info("AI-agent za nekretnine je pokrenut, use_ai=%s", bool(settings.anthropic_api_key))
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
