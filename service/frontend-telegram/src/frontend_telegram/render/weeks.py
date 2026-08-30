import logging
from typing import TYPE_CHECKING
from datetime import date as Date  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812
from functools import partial

from PIL import Image, ImageDraw

from students_schedule import DayType

from .utils import (
    Vector2,
    BoundingBox,
    FormattedScheduleDay,
    ScheduleDayRenderConfig,
    draw_grid,
    draw_text_grid,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from students_schedule import ScheduleDay


logger = logging.getLogger(__name__)


def _draw_day_text_block(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
    text: str,
) -> None:
    border_width = config.border_width
    header_height = config.header_height

    main_text = [text]

    day_bbox = BoundingBox(bbox.x0, bbox.y0, bbox.x1, bbox.y0 + header_height)
    main_bbox = BoundingBox(
        bbox.x0,
        bbox.y0 + header_height - border_width,
        bbox.x1,
        bbox.y1,
    )

    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=config.border_color,
    )

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=config.text_color,
        text_spacing=config.text_spacing,
    )

    _draw_grid(bbox=day_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=main_bbox, size=Vector2(1, 1))

    fday = FormattedScheduleDay(day, config.text_line_max_width)

    _draw_text(
        bbox=day_bbox,
        size=Vector2(1, 1),
        text=fday.day_text,
        font=config.font,
    )
    _draw_text(
        bbox=main_bbox,
        size=Vector2(1, 1),
        text=main_text,
        font=config.font_big,
    )


def _draw_day_normal(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    border_width = config.border_width
    header_height = config.header_height

    day_bbox = BoundingBox(bbox.x0, bbox.y0, bbox.x1, bbox.y0 + header_height)

    classes_bbox = BoundingBox(
        bbox.x0,
        bbox.y0 + header_height - border_width,
        bbox.x1,
        bbox.y1,
    )

    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=config.border_color,
    )

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=config.text_color,
        font=config.font,
        text_spacing=config.text_spacing,
    )

    _draw_grid(bbox=day_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=classes_bbox, size=Vector2(1, 5))

    fday = FormattedScheduleDay(day, config.text_line_max_width)

    _draw_text(bbox=day_bbox, size=Vector2(1, 1), text=fday.day_text)
    _draw_text(
        bbox=classes_bbox,
        size=Vector2(1, 5),
        text=fday.classes_text,
    )


def _draw_day_off(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    _draw_day_text_block(draw, day, config, bbox, config.day_off_text)


def _draw_day_exam(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    raise NotImplementedError


def _draw_day_vacations(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    _draw_day_text_block(draw, day, config, bbox, config.day_vacations_text)


def _draw_day_no_data(
    draw: ImageDraw.ImageDraw,
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    _draw_day_text_block(draw, day, config, bbox, config.day_no_data_text)


def _draw_day_empty(
    draw: ImageDraw.ImageDraw,
    date: Date,
    config: ScheduleDayRenderConfig,
    bbox: BoundingBox,
) -> None:
    border_width = config.border_width
    header_height = config.header_height

    main_text = [date.isoformat()]

    day_bbox = BoundingBox(bbox.x0, bbox.y0, bbox.x1, bbox.y0 + header_height)

    main_bbox = BoundingBox(
        bbox.x0,
        bbox.y0 + header_height - border_width,
        bbox.x1,
        bbox.y1,
    )

    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=config.border_color,
    )

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=config.text_color,
        font=config.font,
        text_spacing=config.text_spacing,
    )

    _draw_grid(bbox=day_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=main_bbox, size=Vector2(1, 1))

    _draw_text(bbox=day_bbox, size=Vector2(1, 1), text=main_text)


def _draw_week(  # noqa: PLR0913, PLR0917
    draw: ImageDraw.ImageDraw,
    days: Sequence[ScheduleDay],
    config: ScheduleDayRenderConfig,
    date_start: Date,
    date_end: Date,
    bbox: BoundingBox,
) -> None:
    border_width = config.border_width
    border_color = config.border_color
    text_color = config.text_color
    text_spacing = config.text_spacing
    font = config.font

    left_column_width = config.left_column_width
    right_column_width = config.right_column_width
    header_height = config.header_height
    main_height = config.main_height

    # Calculate size and coordinates of image components
    week_height: int = header_height + main_height - border_width

    group_bbox = BoundingBox(
        bbox.x0,
        bbox.y0,
        bbox.x0 + left_column_width,
        bbox.y0 + header_height,
    )
    timings_bbox = BoundingBox(
        bbox.x0,
        bbox.y0 + header_height - border_width,
        bbox.x0 + left_column_width,
        bbox.y0 + week_height,
    )

    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=border_color,
    )

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=text_color,
        font=font,
        text_spacing=text_spacing,
    )

    # Draw grid borders
    _draw_grid(bbox=group_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=timings_bbox, size=Vector2(1, 5))

    # Draw class timings text if any day has type `DayType.NORMAL`
    fday = None
    for day in days:
        if day.day_type == DayType.NORMAL:
            fday = FormattedScheduleDay(day, config.text_line_max_width)
            break

    if fday is not None:
        _draw_text(
            bbox=timings_bbox,
            size=Vector2(1, 5),
            text=fday.timings_text,
        )

    # Draw classes blocks
    dates = {day.date: day for day in days}

    for i in range((date_end - date_start).days + 1):
        date = date_start + TimeDelta(days=i)

        offset_x: int = (
            bbox.x0
            + left_column_width
            - border_width
            + (i * (right_column_width - border_width))
        )

        day_bbox = BoundingBox(
            offset_x,
            bbox.y0,
            offset_x + right_column_width,
            bbox.y0 + week_height,
        )

        if date not in dates:
            _draw_day_empty(draw, date, config, day_bbox)
            continue

        day = dates[date]

        match day.day_type:
            case DayType.NORMAL:
                _draw_day_normal(draw, day, config, day_bbox)
            case DayType.DAY_OFF:
                _draw_day_off(draw, day, config, day_bbox)
            case DayType.EXAM:
                _draw_day_exam(draw, day, config, day_bbox)
            case DayType.VACATIONS:
                _draw_day_vacations(draw, day, config, day_bbox)
            case DayType.NO_DATA:
                _draw_day_no_data(draw, day, config, day_bbox)


def render_schedule_weeks(
    days: Sequence[ScheduleDay],
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    # Extract date range for each week
    weeks = []
    for day in days:
        _weekday = day.date.weekday()
        date_start = day.date - TimeDelta(days=_weekday)
        date_end = day.date + TimeDelta(days=(6 - _weekday))

        week = (date_start, date_end)
        if week not in weeks:
            weeks.append(week)

    border_width = config.border_width
    background_color = config.background_color
    border_color = config.border_color
    text_color = config.text_color
    text_spacing = config.text_spacing
    font = config.font

    left_column_width = config.left_column_width
    right_column_width = config.right_column_width
    header_height = config.header_height
    main_height = config.main_height

    # Calculate size and coordinates of all image components
    width: int = left_column_width + (7 * (right_column_width - border_width))
    height: int = (
        len(weeks) * (header_height + main_height - (2 * border_width))
    ) + border_width

    group_bbox = BoundingBox(0, 0, left_column_width, header_height)

    # Create image base
    image = Image.new(
        mode="RGBA",
        size=(width, height),
        color=background_color,
    )

    draw = ImageDraw.Draw(image)

    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=border_color,
    )

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=text_color,
        font=font,
        text_spacing=text_spacing,
    )

    # Draw group block
    fday = FormattedScheduleDay(days[0], config.text_line_max_width)
    _draw_grid(bbox=group_bbox, size=Vector2(1, 1))
    _draw_text(bbox=group_bbox, size=Vector2(1, 1), text=fday.group_text)

    # Draw weeks
    for i, (date_start, date_end) in enumerate(weeks):
        offset_y: int = i * (header_height + main_height - (2 * border_width))

        bbox = BoundingBox(0, offset_y, width, height)

        _draw_week(
            draw=draw,
            days=days,
            config=config,
            date_start=date_start,
            date_end=date_end,
            bbox=bbox,
        )

    return image


def render_schedule_months(
    days: Sequence[ScheduleDay],
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    months = set()
    dates = set()
    for day in days:
        dates.add(day.date)
        months.add((day.date.year, day.date.month))

    # TODO: send multiple images when requested more than one month or
    #       four weeks

    if len(months) == 1:
        return render_schedule_weeks(days, config)

    return Image.new("RGBA", (16, 16), color="#33cc33")
