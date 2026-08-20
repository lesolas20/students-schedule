# type: ignore[ty:invalid-assignment], `getenv_str` and `getenv_int` never return `None` when `required=True`


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
class DatabaseConfig:
    user: str
    password: str
    host: str
    port: int
    name: str


@dataclass(frozen=True)
class Config:
    timezone: ZoneInfo
    schedule: ScheduleConfig
    database: DatabaseConfig


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


def getenv_int(
    key: str,
    default: int | None = None,
    *,
    required: bool = False,
) -> int | None:
    """Get an environment variable representing an `int`, return None
    if it does not exist or is not a valid `int`.
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

    try:
        value_int = int(value)
    except ValueError:
        if not required:
            return default

        msg = f"could not convert value of {key!r} to int: {value!r}"
        raise ValueError(msg) from None

    return value_int


def load_config() -> Config:
    load_dotenv()

    try:
        config_file_path: str = getenv_str("CONFIG_FILE", required=True)
        tz_key: str = getenv_str("TIMEZONE", required=True)
        timezone = ZoneInfo(tz_key)

        # Database config
        db_user: str = getenv_str("DB_USER", required=True)
        db_password: str = getenv_str("DB_PASSWORD", required=True)
        db_host: str = getenv_str("DB_HOST", required=True)
        db_port: int = getenv_int("DB_PORT", required=True)
        db_name: str = getenv_str("DB_NAME", required=True)

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
        database=DatabaseConfig(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            name=db_name,
        ),
    )
