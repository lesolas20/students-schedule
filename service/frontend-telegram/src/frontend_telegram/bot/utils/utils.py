import logging
from enum import Enum
from typing import TYPE_CHECKING
from calendar import monthrange
from datetime import date as Date  # noqa: N812
from datetime import datetime as DateTime  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812

from aiogram.types import (
    User,
    Message,
    BotCommand,
    CallbackQuery,
    InaccessibleMessage,
)
from aiogram.filters.callback_data import CallbackData

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.utils.i18n import I18n


logger = logging.getLogger(__name__)


class ScheduleUnit(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# Callbacks


class RelativeScheduleCallback(CallbackData, prefix="relative-schedule"):
    unit: ScheduleUnit
    delta: int


class AbsoluteScheduleCallback(CallbackData, prefix="absolute-schedule"):
    unit: ScheduleUnit
    date: str


class RangeScheduleCallback(CallbackData, prefix="absolute-schedule"):
    start_date: str
    end_date: str


class SourceCallback(CallbackData, prefix="source"):
    pass


class SelectDateMenuCallback(CallbackData, prefix="select-date-menu"):
    year: int
    month: int


class SelectDateRangeMenuCallback(
    CallbackData,
    prefix="select-date-range-menu",
):
    pass


class MainMenuCallback(CallbackData, prefix="main-menu"):
    pass


class SettingsMenuCallback(CallbackData, prefix="settings-menu"):
    pass


class SelectGroupMenuCallback(CallbackData, prefix="select-group-menu"):
    pass


class SelectYearCallback(CallbackData, prefix="select-year"):
    year: str


class SelectGroupCallback(CallbackData, prefix="select-group"):
    year: str
    group: str


class SelectSubgroupCallback(CallbackData, prefix="select-subgroup"):
    year: str
    group: str
    subgroup: str


class CancelMenuCallback(CallbackData, prefix="cancel-menu"):
    pass


class DummyCallback(CallbackData, prefix="dummy"):
    pass


def today_local() -> Date:
    return DateTime.now().astimezone().date()


def convert_relative_date(
    date: Date,
    unit: ScheduleUnit,
    delta: int,
) -> tuple[Date, Date]:
    """Convert `date`, `unit`, `delta` to a tuple `(date_start, date_end)`"""  # noqa: W505
    match unit:
        case ScheduleUnit.DAY:
            _delta = TimeDelta(days=delta)
            date_start = date + _delta
            date_end = date_start

        case ScheduleUnit.WEEK:
            _weekday = date.weekday()
            _delta = TimeDelta(days=(delta * 7))
            date_start = date - TimeDelta(days=_weekday) + _delta
            date_end = date + TimeDelta(days=(6 - _weekday)) + _delta

        case ScheduleUnit.MONTH:
            max_month: int = 12  # the highest valid value of date.month

            # Calculate the target year and month
            year: int = date.year
            month: int = date.month + delta

            while month < 1:
                year -= 1
                month += max_month

            while month > max_month:
                year += 1
                month -= max_month

            month_length: int = monthrange(year, month)[1]

            date_start = Date(year, month, 1)
            date_end = Date(year, month, month_length)

    return (date_start, date_end)


async def format_user(user: User) -> str:
    """Return a formatted string of main fields from a `User`."""
    user_id = user.id
    user_username = user.username
    user_fullname = user.full_name
    user_language = user.language_code

    return (
        f"id={user_id}, username={user_username!r}, fullname={user_fullname!r}"
        f", language={user_language!r}"
    )


async def format_message(msg: Message) -> str:
    """Return a formatted string of main fields from a `Message`."""
    msg_id = msg.message_id
    msg_date = msg.date
    msg_text = msg.text
    msg_sender = msg.from_user

    if msg_sender is None:
        sender = f"{None!r}"
    else:
        sender = await format_user(msg_sender)

    return (
        f"id={msg_id}, date={msg_date.isoformat()}, text={msg_text!r}"
        f", sender=({sender})"
    )


async def format_query(query: CallbackQuery) -> str:
    """Return a formatted string of main fields from a `CallbackQuery`."""  # noqa: W505
    query_id = query.id
    query_data = query.data
    query_origin = query.message
    query_sender = query.from_user

    if (query_origin is None) or isinstance(query_origin, InaccessibleMessage):
        origin = f"{None!r}"
    else:
        origin = await format_message(query_origin)

    sender = await format_user(query_sender)

    return (
        f"id={query_id}, data={query_data!r}, origin=({origin})"
        f", sender=({sender})"
    )


async def _setup_bot(bot: Bot, i18n: I18n) -> None:
    locale = i18n.current_locale

    if locale == "":
        # Set Telegram locale to "unspecified" and text locale to the
        # default locale
        locale = None
        i18n.current_locale = i18n.default_locale

    _ = i18n.gettext

    bot_name = _("Bot name")
    bot_description = _("Bot description")
    bot_short_description = _("Bot short description")

    cmd_start_desc = _("/start command description")
    cmd_help_desc = _("/help command description")
    cmd_settings_desc = _("/settings command description")
    cmd_today_desc = _("/today command description")
    cmd_tomorrow_desc = _("/tomorrow command description")
    cmd_week_desc = _("/week command description")
    cmd_month_desc = _("/month command description")

    bot_comands = [
        BotCommand(command="start", description=cmd_start_desc),
        BotCommand(command="help", description=cmd_help_desc),
        BotCommand(command="settings", description=cmd_settings_desc),
        BotCommand(command="today", description=cmd_today_desc),
        BotCommand(command="tomorrow", description=cmd_tomorrow_desc),
        BotCommand(command="week", description=cmd_week_desc),
        BotCommand(command="month", description=cmd_month_desc),
    ]

    _old = (await bot.get_my_name(language_code=locale)).name
    _new = bot_name
    if _old != _new:
        logger.debug(f"Bot name was {_old!r}, changing to {_new!r}")
        await bot.set_my_name(_new, language_code=locale)
    else:
        logger.debug(f"Bot name already is {_new!r}")

    _old = (await bot.get_my_description(language_code=locale)).description
    _new = bot_description
    if _old != _new:
        logger.debug(f"Bot description was {_old!r}, changing to {_new!r}")
        await bot.set_my_description(_new, language_code=locale)
    else:
        logger.debug(f"Bot description already is {_new!r}")

    _old = (
        await bot.get_my_short_description(language_code=locale)
    ).short_description
    _new = bot_short_description
    if _old != _new:
        logger.debug(
            f"Bot short description was {_old!r}, changing to {_new!r}",
        )
        await bot.set_my_short_description(_new, language_code=locale)
    else:
        logger.debug(f"Bot short description already is {_new!r}")

    # Bot commands are always updated without checking for changes
    _old = await bot.get_my_commands(language_code=locale)
    _new = bot_comands
    logger.debug(f"Bot commands were {_old!r}, changing to {_new!r}")
    await bot.set_my_commands(_new, language_code=locale)


async def setup_bot(bot: Bot, i18n: I18n) -> None:
    with i18n.use_locale(""):
        logger.info("Setting up bot for unspecified locale")
        await _setup_bot(bot, i18n)

    for locale in i18n.available_locales:
        with i18n.use_locale(locale):
            logger.info(f"Setting up bot for locale {locale!r}")
            await _setup_bot(bot, i18n)
