import logging
import contextlib
from io import BytesIO
from typing import TYPE_CHECKING
from datetime import date as Date  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812

from aiogram import F, Router
from aiogram.types import (
    BufferedInputFile,
    InaccessibleMessage,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.i18n import gettext as _

from frontend_telegram.bot import keyboard
from frontend_telegram.render import (
    ScheduleDayRenderConfig,
    render_schedule,
)
from frontend_telegram.bot.utils import (
    ScheduleUnit,
    DummyCallback,
    SourceCallback,
    MainMenuCallback,
    CancelMenuCallback,
    SelectYearCallback,
    SelectGroupCallback,
    SettingsMenuCallback,
    RangeScheduleCallback,
    SelectDateMenuCallback,
    SelectSubgroupCallback,
    SelectGroupMenuCallback,
    AbsoluteScheduleCallback,
    RelativeScheduleCallback,
    SelectDateRangeMenuCallback,
    today_local,
    format_query,
    format_message,
    convert_relative_date,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aiogram.types import Message, CallbackQuery

    from students_schedule import Group
    from frontend_telegram.config import Config
    from frontend_telegram.database import LocalDatabase, ScheduleDatabase


logger = logging.getLogger(__name__)


router = Router()


# Command handlers


@router.message(CommandStart())
async def command_start(
    message: Message,
    local_database: LocalDatabase,
    config: Config,
) -> None:
    if (
        (message is None)
        or isinstance(message, InaccessibleMessage)
        or (message.from_user is None)
    ):
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved /start command, message=({fmsg})")

    await remove_reply_keyboard(message)

    user_id = message.from_user.id

    if local_database.user_exists(user_id):
        await show_main_menu(message)
    else:
        options = config.ui.groups.keys()
        await show_select_year_menu(message, options, replace=False)


@router.message(Command("help"))
async def command_help(message: Message) -> None:
    fmsg = await format_message(message)
    logger.info(f"Recieved /help command, message=({fmsg})")

    await show_help(message)


@router.message(Command("settings"))
async def command_settings(message: Message) -> None:
    fmsg = await format_message(message)
    logger.info(f"Recieved /settings command, message=({fmsg})")

    await show_settings(message)


@router.message(Command("today"))
async def command_today(
    message: Message,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    if message.from_user is None:
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved /today command, message=({fmsg})")

    user_id = message.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(message, options, replace=False)
        return

    date_start, date_end = convert_relative_date(
        date=today_local(),
        unit=ScheduleUnit.DAY,
        delta=0,
    )

    await show_absolute_schedule(
        message,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )


@router.message(Command("tomorrow"))
async def command_tomorrow(
    message: Message,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    if message.from_user is None:
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved /tomorrow command, message=({fmsg})")

    user_id = message.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(message, options, replace=False)
        return

    date_start, date_end = convert_relative_date(
        date=today_local(),
        unit=ScheduleUnit.DAY,
        delta=1,
    )

    await show_absolute_schedule(
        message,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )


@router.message(Command("week"))
async def command_week(
    message: Message,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    if message.from_user is None:
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved /week command, message=({fmsg})")

    user_id = message.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(message, options, replace=False)
        return

    date_start, date_end = convert_relative_date(
        date=today_local(),
        unit=ScheduleUnit.WEEK,
        delta=0,
    )

    await show_absolute_schedule(
        message,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )


@router.message(Command("month"))
async def command_month(
    message: Message,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    if message.from_user is None:
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved /month command, message=({fmsg})")

    user_id = message.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(message, options, replace=False)
        return

    date_start, date_end = convert_relative_date(
        date=today_local(),
        unit=ScheduleUnit.MONTH,
        delta=0,
    )

    await show_absolute_schedule(
        message,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )


@router.message(F.chat.type == "private")
async def private_message_handler(message: Message) -> None:
    if (message.from_user is None) or (message.from_user.is_bot):
        return

    fmsg = await format_message(message)
    logger.info(f"Recieved private message, message=({fmsg})")


# Callback handlers


@router.callback_query(RelativeScheduleCallback.filter())
async def callback_relative_schedule(
    query: CallbackQuery,
    callback_data: RelativeScheduleCallback,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    msg = query.message

    if (
        (msg is None)
        or isinstance(msg, InaccessibleMessage)
        or (query.from_user is None)
    ):
        return

    fquery = await format_query(query)
    logger.info(f"Recieved relative schedule query, query=({fquery})")

    user_id = query.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(msg, options, replace=False)
        return

    unit = callback_data.unit
    delta = callback_data.delta

    date_start, date_end = convert_relative_date(
        date=today_local(),
        unit=unit,
        delta=delta,
    )

    await show_absolute_schedule(
        msg,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )
    await query.answer()


@router.callback_query(AbsoluteScheduleCallback.filter())
async def callback_absolute_schedule(
    query: CallbackQuery,
    callback_data: AbsoluteScheduleCallback,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        return

    fquery = await format_query(query)
    logger.info(f"Recieved absolute schedule query, query=({fquery})")

    unit = callback_data.unit
    date = Date.fromisoformat(callback_data.date)

    user_id = query.from_user.id
    group = local_database.get_user_group(user_id=user_id)

    if group is None:
        options = config.ui.groups.keys()
        await show_select_year_menu(msg, options, replace=False)
        return

    date_start, date_end = convert_relative_date(
        date=date,
        unit=unit,
        delta=0,
    )

    await show_absolute_schedule(
        msg,
        schedule_database,
        group,
        date_start,
        date_end,
        config.render,
    )

    await query.answer()


@router.callback_query(RangeScheduleCallback.filter())
async def callback_range_schedule(
    query: CallbackQuery,
    callback_data: RangeScheduleCallback,  # noqa: ARG001
) -> None:
    await query.answer()
    # TODO: implement, low priority


@router.callback_query(SourceCallback.filter())
async def callback_source(query: CallbackQuery, config: Config) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved source query, query=({fquery})")

    text = _("Link to the data source:\n{url}").format(
        url=config.schedule.display_url,
    )
    await msg.answer(text)
    await query.answer()


@router.callback_query(SelectDateMenuCallback.filter())
async def callback_select_date_menu(
    query: CallbackQuery,
    callback_data: SelectDateMenuCallback,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved select date menu query, query=({fquery})")

    year = callback_data.year
    month = callback_data.month

    if year == 0:
        year = None
    if month == 0:
        month = None

    await show_select_date_menu(msg, year, month)
    await query.answer()


@router.callback_query(SelectDateRangeMenuCallback.filter())
async def callback_select_date_range_menu(query: CallbackQuery) -> None:
    await query.answer()
    # TODO: implement, low priority


@router.callback_query(MainMenuCallback.filter())
async def callback_main_menu(query: CallbackQuery) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved main menu query, query=({fquery})")

    await show_main_menu(msg)
    await query.answer()


@router.callback_query(SettingsMenuCallback.filter())
async def callback_settings_menu(query: CallbackQuery) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved settings menu query, query=({fquery})")

    await show_settings(msg)
    await query.answer()


@router.callback_query(SelectGroupMenuCallback.filter())
async def callback_select_group_menu(
    query: CallbackQuery,
    config: Config,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved select group menu query, query=({fquery})")

    options = config.ui.groups.keys()
    await show_select_year_menu(msg, options)
    await query.answer()


@router.callback_query(SelectYearCallback.filter())
async def callback_select_year(
    query: CallbackQuery,
    callback_data: SelectYearCallback,
    config: Config,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved select year query, query=({fquery})")

    year = callback_data.year
    options = config.ui.groups[year].keys()
    await show_select_group_menu(msg, options, year)
    await query.answer()


@router.callback_query(SelectGroupCallback.filter())
async def callback_select_group(
    query: CallbackQuery,
    callback_data: SelectGroupCallback,
    local_database: LocalDatabase,
    config: Config,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        return

    fquery = await format_query(query)
    logger.info(f"Recieved select group query, query=({fquery})")

    year = callback_data.year
    group = callback_data.group
    options = config.ui.groups[year][group]

    if len(options) == 1:
        # When there is only a single subgroup in a group, skip subgroup
        # selection
        subgroup = options[0]

        user_id = query.from_user.id

        local_database.insert_or_update_user(user_id=user_id, group=subgroup)

        text = _("Selected group {group}").format(group=subgroup)
        await msg.edit_text(text)
        await show_main_menu(msg)
        await query.answer()

        return

    await show_select_subgroup_menu(msg, options, year, group)
    await query.answer()


@router.callback_query(SelectSubgroupCallback.filter())
async def callback_select_subgroup(
    query: CallbackQuery,
    callback_data: SelectSubgroupCallback,
    local_database: LocalDatabase,
) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        return

    fquery = await format_query(query)
    logger.info(f"Recieved select subgroup query, query=({fquery})")

    subgroup = callback_data.subgroup

    user_id = query.from_user.id

    local_database.insert_or_update_user(user_id=user_id, group=subgroup)

    text = _("Selected group {group}").format(group=subgroup)
    await msg.edit_text(text)
    await show_main_menu(msg)
    await query.answer()


@router.callback_query(CancelMenuCallback.filter())
async def callback_cancel_menu(query: CallbackQuery) -> None:
    msg = query.message

    if (msg is None) or isinstance(msg, InaccessibleMessage):
        await query.answer()
        return

    fquery = await format_query(query)
    logger.info(f"Recieved cancel menu query, query=({fquery})")

    with contextlib.suppress(TelegramBadRequest):
        await msg.delete()

    await query.answer()


@router.callback_query(DummyCallback.filter())
async def callback_dummy(query: CallbackQuery) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved dummy query, query=({fquery})")

    await query.answer()


# Handlers


async def remove_reply_keyboard(message: Message) -> None:
    """Remove the current reply keyboard if it exists."""
    # There is no way to delete a reply keyboard without sending a
    # message, so we send a message removing the keyboard and
    # immediately delete that message
    tmp_msg = await message.answer(".", reply_markup=ReplyKeyboardRemove())
    with contextlib.suppress(TelegramBadRequest):
        await tmp_msg.delete()


async def show_main_menu(message: Message) -> None:
    keyboard_markup = keyboard.main_menu()
    menu = await message.answer(
        _("Main menu text"),
        reply_markup=keyboard_markup,
    )
    await menu.pin()


async def show_help(message: Message) -> None:
    # TR: help text should include full bot description
    await message.answer(_("Help text"))


async def show_settings(message: Message) -> None:
    keyboard_markup = keyboard.settings_menu()
    await message.answer(_("Settings menu text"), reply_markup=keyboard_markup)


async def show_select_year_menu(
    message: Message,
    options: Iterable[str],
    *,
    replace: bool = True,
) -> None:
    text = _("Year selection menu text")
    keyboard_markup = keyboard.select_year_menu(options)

    if replace:
        await message.edit_text(text)
        await message.edit_reply_markup(reply_markup=keyboard_markup)
    else:
        await message.answer(text, reply_markup=keyboard_markup)


async def show_select_group_menu(
    message: Message,
    options: Iterable[str],
    selected_year: str,
) -> None:
    keyboard_markup = keyboard.select_group_menu(options, selected_year)
    await message.edit_text(_("Group selection menu text"))
    await message.edit_reply_markup(reply_markup=keyboard_markup)


async def show_select_subgroup_menu(
    message: Message,
    options: Iterable[str],
    selected_year: str,
    selected_group: str,
) -> None:
    keyboard_markup = keyboard.select_subgroup_menu(
        options,
        selected_year,
        selected_group,
    )
    await message.edit_text(_("Subgroup selection menu text"))
    await message.edit_reply_markup(reply_markup=keyboard_markup)


async def show_select_date_menu(
    message: Message,
    year: int | None = None,
    month: int | None = None,
) -> None:
    today = today_local()

    # Get the first day in the month (month_first_date)
    mfd = Date(year=today.year, month=today.month, day=1)

    text = _("Select date menu text")

    if (year is None) or (month is None):
        keyboard_markup = keyboard.select_date_menu(
            today,
            previous=True,
            following=True,
        )
        await message.answer(text, reply_markup=keyboard_markup)

    else:
        date = Date(year=year, month=month, day=1)
        keyboard_markup = keyboard.select_date_menu(
            date,
            previous=(mfd - date) <= TimeDelta(days=28 * 2),
            following=(date - mfd) <= TimeDelta(days=28 * 2),
        )
        await message.edit_text(text)
        await message.edit_reply_markup(reply_markup=keyboard_markup)


async def show_absolute_schedule(  # noqa: PLR0913, PLR0917
    message: Message,
    database: ScheduleDatabase,
    group: Group,
    date_start: Date,
    date_end: Date,
    render_config: ScheduleDayRenderConfig,
) -> None:
    prefer_photo_max_image_size: int = 5000
    prefer_photo_max_image_ratio: int = 4

    await message.chat.do(action="upload_photo")

    days = await database.load_schedule_days(group, date_start, date_end)

    image = render_schedule(days, render_config)

    image_buffer = BytesIO()
    image.save(image_buffer, format="png")
    image_bytes = image_buffer.getvalue()

    logger.info(
        f"Sending a schedule image {image.width}x{image.height}"
        f", {len(image_bytes)} bytes",
    )

    file = BufferedInputFile(
        file=image_bytes,
        filename=_("Schedule image filename"),
    )

    if (
        ((image.width + image.height) > prefer_photo_max_image_size)
        or (1 > (image.width / image.height) > prefer_photo_max_image_ratio)
        or (1 > (image.height / image.width) > prefer_photo_max_image_ratio)
    ):
        await message.answer_document(file)
    else:
        await message.answer_photo(file)
