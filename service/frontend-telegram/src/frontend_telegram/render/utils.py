import logging
import textwrap
from typing import TYPE_CHECKING
from functools import partial, cached_property
from itertools import product
from dataclasses import dataclass

from PIL import ImageDraw, ImageFont

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Sequence

    from students_schedule import ScheduleDay

from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

type Ink = str
type Font = (
    ImageFont.ImageFont | ImageFont.FreeTypeFont | ImageFont.TransposedFont
)


@dataclass(frozen=True)
class Vector2:
    x: int
    y: int


@dataclass(frozen=True)
class BoundingBox:
    x0: int
    y0: int
    x1: int
    y1: int


@dataclass(frozen=True)
class ScheduleDayRenderConfig:
    border_width: int
    background_color: Ink
    border_color: Ink

    text_color: Ink
    font_path: Path
    font_size: int
    font_size_big: int
    text_spacing: float

    left_column_width: int
    right_column_width: int
    header_height: int
    main_height: int

    text_line_max_width: int
    day_off_text: str
    day_vacations_text: str
    day_no_data_text: str

    @cached_property
    def font(self) -> Font:
        return ImageFont.truetype(font=self.font_path, size=self.font_size)

    @cached_property
    def font_big(self) -> Font:
        return ImageFont.truetype(font=self.font_path, size=self.font_size_big)


@dataclass
class FormattedScheduleDay:
    def __init__(self, day: ScheduleDay, text_line_max_width: int) -> None:
        wrap = partial(
            textwrap.fill,
            width=text_line_max_width,
            expand_tabs=False,
            replace_whitespace=False,
            break_long_words=False,
            break_on_hyphens=False,
        )

        self.group_text = [day.group]
        self.day_text = [day.date.isoformat()]

        timings_text = []
        classes_text = []

        for c in day.classes:
            t_text = (
                f"{c.time.class_start} – {c.time.break_start}"  # noqa: RUF001
                f"\n{c.time.break_end} – {c.time.class_end}"  # noqa: RUF001
            )

            c_text_parts = []

            if c.subject is not None:
                c_text_parts.append(wrap(c.subject))

            if c.professor is not None:
                c_text_parts.append(c.professor)

            if c.room is not None:
                c_text_parts.append(c.room)

            if len(c.groups) > 1:
                c_text_parts.append(wrap(", ".join(c.groups)))

            classes_text.append("\n".join(c_text_parts))
            timings_text.append(t_text)

        self.timings_text = timings_text
        self.classes_text = classes_text


def draw_grid(
    draw: ImageDraw.ImageDraw,
    bbox: BoundingBox,
    size: Vector2,
    line_width: int = 1,
    line_color: Ink | None = None,
) -> None:
    """Using `draw`, draw size `size` grid contained by coordinates
    `bbox`. Line thickness is defined by `line_width` ≥1.
    """
    width: int = bbox.x1 - bbox.x0
    height: int = bbox.y1 - bbox.y0

    lines_x: int = size.x + 1
    lines_y: int = size.y + 1

    line_spacing_x: float = (width - (lines_x * line_width)) / size.x
    line_spacing_y: float = (height - (lines_y * line_width)) / size.y

    # Draw vertical grid lines
    for i in range(lines_x):
        x0: float = bbox.x0 + ((line_width * i) + (line_spacing_x * i))
        y0: int = bbox.y0
        x1: float = x0 + line_width - 1
        y1: int = bbox.y1 - 1

        pos = (x0, y0, x1, y1)
        draw.rectangle(pos, fill=line_color)

    # Draw horizontal grid lines
    for i in range(lines_y):
        x0: int = bbox.x0
        y0: float = bbox.y0 + ((line_width * i) + (line_spacing_y * i))
        x1: int = bbox.x1 - 1
        y1: float = y0 + line_width - 1

        pos = (x0, y0, x1, y1)
        draw.rectangle(pos, fill=line_color)


def draw_text_grid(  # noqa: PLR0913, PLR0917
    draw: ImageDraw.ImageDraw,
    bbox: BoundingBox,
    size: Vector2,
    text: Sequence[str],
    border_width: int = 1,
    text_color: Ink | None = None,
    font: Font | None = None,
    text_spacing: float = 4,
) -> None:
    """Using `draw`, draw size `size` grid contained by coordinates
    `bbox`. Each cell of the grid contains text from `text[i]`. Text is
    centered in each cell. Border thickness is defined by
    `border_width` ≥1.
    """
    width: int = bbox.x1 - bbox.x0
    height: int = bbox.y1 - bbox.y0

    lines_x: int = size.x + 1
    lines_y: int = size.y + 1

    line_spacing_x: float = (width - (lines_x * border_width)) / size.x
    line_spacing_y: float = (height - (lines_y * border_width)) / size.y

    for i, (cell_y, cell_x) in enumerate(
        product(range(size.y), range(size.x)),
    ):
        x0: float = bbox.x0 + (
            (border_width * (cell_x + 1)) + (line_spacing_x * cell_x)
        )
        y0: float = bbox.y0 + (
            (border_width * (cell_y + 1)) + (line_spacing_y * cell_y)
        )
        x1: float = x0 + line_spacing_x - 1
        y1: float = y0 + line_spacing_y - 1

        xc: float = (x0 + x1) // 2
        yc: float = (y0 + y1) // 2

        pos = (xc, yc)

        draw.text(
            pos,
            text=text[i],
            fill=text_color,
            font=font,
            anchor="mm",
            spacing=text_spacing,
            align="center",
        )
