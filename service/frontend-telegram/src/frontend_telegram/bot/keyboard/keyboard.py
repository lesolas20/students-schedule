import logging
from typing import TYPE_CHECKING
from calendar import Day, Month, Calendar
from datetime import date as Date  # noqa: N812

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from frontend_telegram.bot.utils import (
    ScheduleUnit,
    DummyCallback,
    SourceCallback,
    CancelMenuCallback,
    SelectYearCallback,
    SelectGroupCallback,
    SettingsMenuCallback,
    SelectDateMenuCallback,
    SelectSubgroupCallback,
    SelectGroupMenuCallback,
    AbsoluteScheduleCallback,
    RelativeScheduleCallback,
    SelectDateRangeMenuCallback,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Iterable, Sequence


logger = logging.getLogger(__name__)


def main_menu() -> InlineKeyboardMarkup:
    today_button = InlineKeyboardButton(
        text=_("Schedule for today"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.DAY,
            delta=0,
        ).pack(),
    )
    tomorrow_button = InlineKeyboardButton(
        text=_("Schedule for tomorrow"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.DAY,
            delta=1,
        ).pack(),
    )
    this_week_button = InlineKeyboardButton(
        text=_("Schedule for this week"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.WEEK,
            delta=0,
        ).pack(),
    )
    next_week_button = InlineKeyboardButton(
        text=_("Schedule for the next week"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.WEEK,
            delta=1,
        ).pack(),
    )
    this_month_button = InlineKeyboardButton(
        text=_("Schedule for this month"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.MONTH,
            delta=0,
        ).pack(),
    )
    next_month_button = InlineKeyboardButton(
        text=_("Schedule for the next month"),
        callback_data=RelativeScheduleCallback(
            unit=ScheduleUnit.MONTH,
            delta=1,
        ).pack(),
    )
    select_date_button = InlineKeyboardButton(
        text=_("Schedule for the selected date"),
        callback_data=SelectDateMenuCallback(year=0, month=0).pack(),
    )
    select_date_range_button = InlineKeyboardButton(
        text=_("Schedule for the selected range of dates"),
        callback_data=SelectDateRangeMenuCallback().pack(),
    )
    settings_button = InlineKeyboardButton(
        text=_("Settings menu"),
        callback_data=SettingsMenuCallback().pack(),
    )
    source_button = InlineKeyboardButton(
        text=_("Link to the data source"),
        callback_data=SourceCallback().pack(),
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [today_button, tomorrow_button],
            [this_week_button, next_week_button],
            [this_month_button, next_month_button],
            [select_date_button],
            # [select_date_range_button],
            [settings_button],
            [source_button],
        ],
    )


def settings_menu() -> InlineKeyboardMarkup:
    change_group_button = InlineKeyboardButton(
        text=_("Change group menu"),
        callback_data=SelectGroupMenuCallback().pack(),
    )
    cancel_button = InlineKeyboardButton(
        text=_("Cancel menu"),
        callback_data=CancelMenuCallback().pack(),
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [change_group_button],
            [cancel_button],
        ],
    )


def select_year_menu(options: Iterable[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for option in options:
        builder.button(
            text=_(option),
            callback_data=SelectYearCallback(year=option).pack(),
        )

    cancel_button = InlineKeyboardButton(
        text=_("Cancel menu"),
        callback_data=CancelMenuCallback().pack(),
    )
    builder.add(cancel_button)

    builder.adjust(1, repeat=True)

    return builder.as_markup()


def select_group_menu(
    options: Iterable[str],
    selected_year: str,
) -> InlineKeyboardMarkup:
    width: int = 4

    cancel_button = InlineKeyboardButton(
        text=_("Cancel menu"),
        callback_data=CancelMenuCallback().pack(),
    )

    dummy_button = InlineKeyboardButton(
        text=" ",
        callback_data=DummyCallback().pack(),
    )

    builder = InlineKeyboardBuilder()

    for option in options:
        builder.button(
            text=_(option),
            callback_data=SelectGroupCallback(
                year=selected_year,
                group=option,
            ).pack(),
        )

    last_row_buttons_count = len(tuple(builder.buttons)) % width
    if last_row_buttons_count != 0:
        empty_buttons_count = width - last_row_buttons_count

        for _i in range(empty_buttons_count):
            builder.add(dummy_button)

    builder.adjust(width, repeat=True)

    builder.row(cancel_button, width=1)

    return builder.as_markup()


def select_subgroup_menu(
    options: Iterable[str],
    selected_year: str,
    selected_group: str,
) -> InlineKeyboardMarkup:
    width: int = 4

    cancel_button = InlineKeyboardButton(
        text=_("Cancel menu"),
        callback_data=CancelMenuCallback().pack(),
    )

    dummy_button = InlineKeyboardButton(
        text=" ",
        callback_data=DummyCallback().pack(),
    )

    builder = InlineKeyboardBuilder()

    for option in options:
        builder.button(
            text=_(option),
            callback_data=SelectSubgroupCallback(
                year=selected_year,
                group=selected_group,
                subgroup=option,
            ).pack(),
        )

    last_row_buttons_count = len(tuple(builder.buttons)) % width
    if last_row_buttons_count != 0:
        empty_buttons_count = width - last_row_buttons_count

        for _i in range(empty_buttons_count):
            builder.add(dummy_button)

    builder.adjust(width, repeat=True)

    builder.row(cancel_button, width=1)

    return builder.as_markup()


def select_date_menu(  # noqa: C901, PLR0912, PLR0915
    date: Date,
    *,
    previous: bool,
    following: bool,
) -> InlineKeyboardMarkup:
    month_starts_on_weekend: bool = Date(
        date.year,
        date.month,
        1,
    ).weekday() in {
        Day.SATURDAY,
        Day.SUNDAY,
    }

    cancel_button = InlineKeyboardButton(
        text=_("Cancel menu"),
        callback_data=CancelMenuCallback().pack(),
    )

    dummy_button = InlineKeyboardButton(
        text=" ",
        callback_data=DummyCallback().pack(),
    )

    builder = InlineKeyboardBuilder()

    month_name = Month(date.month).name.capitalize()
    month_text = _(f"{month_name} long")
    year_text = f"{date.year}"

    builder.button(
        text=_("Select date menu header {month} {year}").format(
            month=month_text,
            year=year_text,
        ),
        callback_data=DummyCallback().pack(),
    )

    if previous:
        year, month = _bound_date(date.year, date.month - 1)
        builder.button(
            text=_("Previous month"),
            callback_data=SelectDateMenuCallback(
                year=year,
                month=month,
            ).pack(),
        )
    else:
        builder.add(dummy_button)

    if following:
        year, month = _bound_date(date.year, date.month + 1)
        builder.button(
            text=_("Following month"),
            callback_data=SelectDateMenuCallback(
                year=year,
                month=month,
            ).pack(),
        )
    else:
        builder.add(dummy_button)

    builder.button(
        text=_("Show entire month"),
        callback_data=AbsoluteScheduleCallback(
            unit=ScheduleUnit.MONTH,
            date=date.isoformat(),
        ).pack(),
    )

    # Add week days header
    for weekday in Day:
        if weekday in {Day.SATURDAY, Day.SUNDAY}:
            continue

        weekday_name = weekday.name.capitalize()
        weekday_text = _(f"{weekday_name} short")

        builder.button(
            text=weekday_text,
            callback_data=DummyCallback().pack(),
        )

    builder.add(dummy_button)

    month_days = Calendar().itermonthdays2(
        year=date.year,
        month=date.month,
    )

    weeks: Mapping[int, Sequence[tuple[int, int]]] = {}
    week: int = 0
    for day, weekday in month_days:
        if weekday == Day.MONDAY:
            weeks[week] = []

        weeks[week].append((day, weekday))

        if weekday == Day.SUNDAY:
            week += 1

    # Add days
    for week, week_days in weeks.items():
        week_date = None

        if month_starts_on_weekend and (week == 0):
            continue

        for day, weekday in week_days:
            # Skip weekends
            if weekday in {Day.SATURDAY, Day.SUNDAY}:
                continue

            # Do not show days beyond the current month
            if day == 0:
                builder.add(dummy_button)

            else:
                # Add day button
                text = f"{day}"
                _date = Date(year=date.year, month=date.month, day=day)

                callback_data = AbsoluteScheduleCallback(
                    unit=ScheduleUnit.DAY,
                    date=_date.isoformat(),
                ).pack()
                builder.button(text=text, callback_data=callback_data)

                if week_date is None:
                    week_date = _date

            # Add week button
            if weekday == Day.FRIDAY:
                if week_date is None:
                    builder.add(dummy_button)

                else:
                    # TR: This text should be as short as possible,
                    #     preferably under 7 characters
                    text = _("Show entire week")

                    callback_data = AbsoluteScheduleCallback(
                        unit=ScheduleUnit.WEEK,
                        date=week_date.isoformat(),
                    ).pack()
                    builder.button(text=text, callback_data=callback_data)

    builder.adjust(1, 2, 1, 6)

    builder.row(cancel_button, width=1)

    return builder.as_markup()


def _bound_date(year: int, month: int) -> tuple[int, int]:
    max_month: int = 12  # the highest valid value of date.month

    while month < 1:
        year -= 1
        month += max_month

    while month > max_month:
        year += 1
        month -= max_month

    return (year, month)
