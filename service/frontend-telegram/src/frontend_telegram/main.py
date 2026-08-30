import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware

from utils import setup_logging
from frontend_telegram.compat import router as router_compat
from frontend_telegram.config import load_config
from frontend_telegram.database import LocalDatabase, ScheduleDatabase
from frontend_telegram.handlers import router
from frontend_telegram.bot.utils import setup_bot

if __name__ == "__main__":
    setup_logging(logging.DEBUG)

    config = load_config()

    local_database = LocalDatabase(
        file=config.local_database.file,
        db_init_script=config.local_database.init_script,
    )
    schedule_database = ScheduleDatabase(
        config.schedule_database.user,
        config.schedule_database.password,
        config.schedule_database.host,
        config.schedule_database.port,
        config.schedule_database.name,
    )

    bot = Bot(token=config.bot.token)

    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher.include_router(router_compat)

    i18n = I18n(path=Path("locales"), default_locale="en")
    i18n_middleware = SimpleI18nMiddleware(i18n)
    i18n_middleware.setup(dispatcher)

    async def _run_bot() -> None:
        await setup_bot(bot, i18n)

        await dispatcher.start_polling(
            bot,
            config=config,
            local_database=local_database,
            schedule_database=schedule_database,
        )

    asyncio.run(_run_bot())
