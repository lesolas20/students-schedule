import logging
from typing import TYPE_CHECKING, Any
from datetime import datetime as DateTime  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812

from aiogram import BaseMiddleware
from aiogram.types import Message

from frontend_telegram.bot.utils import format_message

if TYPE_CHECKING:
    from collections.abc import Callable, Awaitable

    from aiogram.types import TelegramObject


logger = logging.getLogger(__name__)


class EventTimeoutMiddleware(BaseMiddleware):
    def __init__(self, event_timeout: TimeDelta) -> None:
        self.event_timeout = event_timeout

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:  # noqa: ANN401
        if not isinstance(event, Message):
            return await handler(event, data)

        delta = DateTime.now().astimezone() - event.date
        if delta > self.event_timeout:
            fmsg = await format_message(event)
            logger.info(
                f"Ignoring old event from {delta} ago, message=({fmsg})",
            )
            return None

        return await handler(event, data)
