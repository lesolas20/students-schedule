# type: ignore[ty:invalid-assignment], `getenv_str` never returns `None` when `required=True`


import logging
import tomllib
import traceback
from os import getenv
from typing import TYPE_CHECKING
from pathlib import Path
from zoneinfo import ZoneInfo
from dataclasses import dataclass

from dotenv import load_dotenv

if TYPE_CHECKING:
    from datetime import date as Date  # noqa: N812


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScheduleConfig:
    url: str
    display_url: str
    semester_start_date: Date
    schedule_day_range_start: int
    schedule_day_range_end: int


@dataclass(frozen=True)
class Config:
    timezone: ZoneInfo
    schedule: ScheduleConfig


def getenv_str(
    key: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str | None:
    """Get an environment variable representing a `str`, return `None`
    if it does not exist.
    The optional argument `default` can specify a different value
    to return on failure.
    If `required` is set to `True`, raise `ValueError` on failure
    instead of returning `default`.
    """
    value = getenv(key)

    if value is None:
        if not required:
            return default

        msg = f"could not get value of {key!r} which is required"
        raise ValueError(msg) from None

    return value


def load_config() -> Config:
    load_dotenv()

    try:
        config_file_path: str = getenv_str("CONFIG_FILE", required=True)
        tz_key: str = getenv_str("TIMEZONE", required=True)
        timezone = ZoneInfo(tz_key)

    except ValueError as e:
        logger.info(f"Loading config failed with {e!r}")
        logger.debug(traceback.format_exc())
        raise

    with Path(config_file_path).open("rb") as file:
        config = tomllib.load(file)

    return Config(
        timezone=timezone,
        schedule=ScheduleConfig(
            url=config["schedule"]["url"],
            display_url=config["schedule"]["display-url"],
            semester_start_date=config["schedule"]["semester-start-date"],
            schedule_day_range_start=config["schedule"][
                "schedule-day-range-start"
            ],
            schedule_day_range_end=config["schedule"][
                "schedule-day-range-end"
            ],
        ),
    )
