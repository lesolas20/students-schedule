import logging
from typing import TYPE_CHECKING

from .day import render_schedule_day
from .weeks import render_schedule_weeks

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PIL import Image

    from students_schedule import ScheduleDay

    from .utils import ScheduleDayRenderConfig


logger = logging.getLogger(__name__)


def render_schedule(
    days: Sequence[ScheduleDay],
    config: ScheduleDayRenderConfig,
) -> Image.Image:
    if len(days) == 1:
        return render_schedule_day(days[0], config)

    return render_schedule_weeks(days, config)
