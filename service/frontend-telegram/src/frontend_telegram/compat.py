import logging
from typing import TYPE_CHECKING
from datetime import date as Date  # noqa: N812

from aiogram import Router
from aiogram.filters.callback_data import CallbackData

from frontend_telegram.handlers import (
    callback_dummy,
    callback_source,
    callback_main_menu,
    callback_select_date_menu,
    callback_absolute_schedule,
    callback_relative_schedule,
    callback_select_group_menu,
)
from frontend_telegram.bot.utils import (
    ScheduleUnit,
    SelectDateMenuCallback,
    AbsoluteScheduleCallback,
    RelativeScheduleCallback,
    format_query,
)

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

    from frontend_telegram.config import Config
    from frontend_telegram.database import LocalDatabase, ScheduleDatabase


logger = logging.getLogger(__name__)


router = Router()


class DeltaScheduleCallbackCompat(CallbackData, prefix="delta_schedule"):
    day_delta: int


class DateScheduleCallbackCompat(CallbackData, prefix="date_schedule"):
    date: str


class SelectDateMenuCallbackCompat(CallbackData, prefix="select_date"):
    pass


class SelectGroupMenuCallbackCompat(CallbackData, prefix="select_group"):
    course: str
    group: str
    subgroup: str


class GetSourceCallbackCompat(CallbackData, prefix="get_source"):
    pass


class MainMenuCallbackCompat(CallbackData, prefix="main_menu"):
    pass


class NoOpCallbackCompat(CallbackData, prefix="no_op"):
    pass


# Callback handlers


@router.callback_query(DeltaScheduleCallbackCompat.filter())
async def callback_relative_schedule_compat(
    query: CallbackQuery,
    callback_data: DeltaScheduleCallbackCompat,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved relative schedule compat query, query=({fquery})")

    delta = callback_data.day_delta
    _callback_data = RelativeScheduleCallback(
        unit=ScheduleUnit.DAY,
        delta=delta,
    )
    await callback_relative_schedule(
        query,
        _callback_data,
        local_database,
        schedule_database,
        config,
    )


@router.callback_query(DateScheduleCallbackCompat.filter())
async def callback_absolute_schedule_compat(
    query: CallbackQuery,
    callback_data: DateScheduleCallbackCompat,
    local_database: LocalDatabase,
    schedule_database: ScheduleDatabase,
    config: Config,
) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved absolute schedule compat query, query=({fquery})")

    date = Date.strptime(callback_data.date, "%d-%m-%Y").isoformat()
    _callback_data = AbsoluteScheduleCallback(
        unit=ScheduleUnit.DAY,
        date=date,
    )
    await callback_absolute_schedule(
        query,
        _callback_data,
        local_database,
        schedule_database,
        config,
    )


@router.callback_query(SelectDateMenuCallbackCompat.filter())
async def callback_select_date_menu_compat(query: CallbackQuery) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved select date menu compat query, query=({fquery})")

    _callback_data = SelectDateMenuCallback(year=0, month=0)
    await callback_select_date_menu(query, _callback_data)


@router.callback_query(SelectGroupMenuCallbackCompat.filter())
async def callback_select_group_compat(
    query: CallbackQuery,
    config: Config,
) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved select group compat query, query=({fquery})")

    await callback_select_group_menu(query, config)


@router.callback_query(GetSourceCallbackCompat.filter())
async def callback_source_compat(query: CallbackQuery, config: Config) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved source compat query, query=({fquery})")

    await callback_source(query, config)


@router.callback_query(MainMenuCallbackCompat.filter())
async def callback_main_menu_compat(query: CallbackQuery) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved main menu compat query, query=({fquery})")

    await callback_main_menu(query)


@router.callback_query(NoOpCallbackCompat.filter())
async def callback_dummy_compat(query: CallbackQuery) -> None:
    fquery = await format_query(query)
    logger.info(f"Recieved dummy compat query, query=({fquery})")

    await callback_dummy(query)
