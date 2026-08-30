import logging
from typing import TYPE_CHECKING
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
    from students_schedule import ScheduleDay


logger = logging.getLogger(__name__)


def _render_schedule_day_text_block(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
    text: str,
) -> Image.Image:
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

    main_text = [text]

    # Calculate size and coordinates of all image components
    width: int = left_column_width + right_column_width - border_width
    height: int = header_height + main_height - border_width

    x0: int = left_column_width - border_width
    y0: int = header_height - border_width

    group_bbox = BoundingBox(0, 0, left_column_width, header_height)
    day_bbox = BoundingBox(x0, 0, width, header_height)
    main_bbox = BoundingBox(0, y0, width, height)

    # Create image base
    image = Image.new(
        mode="RGBA",
        size=(width, height),
        color=background_color,
    )

    draw = ImageDraw.Draw(image)

    # Draw image borders
    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=border_color,
    )

    _draw_grid(bbox=group_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=day_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=main_bbox, size=Vector2(1, 1))

    # Draw text
    fday = FormattedScheduleDay(day, config.text_line_max_width)

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=text_color,
        text_spacing=text_spacing,
    )

    _draw_text(
        bbox=group_bbox,
        size=Vector2(1, 1),
        text=fday.group_text,
        font=font,
    )
    _draw_text(
        bbox=day_bbox,
        size=Vector2(1, 1),
        text=fday.day_text,
        font=font,
    )
    _draw_text(
        bbox=main_bbox,
        size=Vector2(1, 1),
        text=main_text,
        font=config.font_big,
    )

    return image


def _render_schedule_day_normal(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
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
    width: int = left_column_width + right_column_width - border_width
    height: int = header_height + main_height - border_width

    x0: int = left_column_width - border_width
    y0: int = header_height - border_width

    group_bbox = BoundingBox(0, 0, left_column_width, header_height)
    day_bbox = BoundingBox(x0, 0, width, header_height)
    timings_bbox = BoundingBox(0, y0, left_column_width, height)
    classes_bbox = BoundingBox(x0, y0, width, height)

    # Create image base
    image = Image.new(
        mode="RGBA",
        size=(width, height),
        color=background_color,
    )

    draw = ImageDraw.Draw(image)

    # Draw grid borders
    _draw_grid = partial(
        draw_grid,
        draw=draw,
        line_width=border_width,
        line_color=border_color,
    )

    _draw_grid(bbox=group_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=day_bbox, size=Vector2(1, 1))
    _draw_grid(bbox=timings_bbox, size=Vector2(1, 5))
    _draw_grid(bbox=classes_bbox, size=Vector2(1, 5))

    # Draw text
    fday = FormattedScheduleDay(day, config.text_line_max_width)

    _draw_text = partial(
        draw_text_grid,
        draw=draw,
        border_width=border_width,
        text_color=text_color,
        font=font,
        text_spacing=text_spacing,
    )

    _draw_text(bbox=group_bbox, size=Vector2(1, 1), text=fday.group_text)
    _draw_text(bbox=day_bbox, size=Vector2(1, 1), text=fday.day_text)
    _draw_text(bbox=timings_bbox, size=Vector2(1, 5), text=fday.timings_text)
    _draw_text(bbox=classes_bbox, size=Vector2(1, 5), text=fday.classes_text)

    return image


def _render_schedule_day_off(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    return _render_schedule_day_text_block(day, config, config.day_off_text)


def _render_schedule_day_vacations(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    return _render_schedule_day_text_block(
        day,
        config,
        config.day_vacations_text,
    )


def _render_schedule_day_no_data(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    return _render_schedule_day_text_block(
        day,
        config,
        config.day_no_data_text,
    )


def _render_schedule_day_exam(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    raise NotImplementedError


def render_schedule_day(
    day: ScheduleDay,
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    match day.day_type:
        case DayType.NORMAL:
            return _render_schedule_day_normal(day, config)
        case DayType.DAY_OFF:
            return _render_schedule_day_off(day, config)
        case DayType.EXAM:
            return _render_schedule_day_exam(day, config)
        case DayType.VACATIONS:
            return _render_schedule_day_vacations(day, config)
        case DayType.NO_DATA:
            return _render_schedule_day_no_data(day, config)
