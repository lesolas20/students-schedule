# type: ignore[ty:invalid-assignment], `getenv_str` and `getenv_int` never return `None` when `required=True`

import logging
import tomllib
import traceback
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import timedelta as TimeDelta  # noqa: N812
from dataclasses import dataclass

from dotenv import load_dotenv

from utils import getenv_int, getenv_str
from frontend_telegram.render import ScheduleDayRenderConfig

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotConfig:
    token: str


@dataclass(frozen=True)
class MiscellaneousConfig:
    event_timeout: TimeDelta


@dataclass(frozen=True)
class ScheduleConfig:
    display_url: str


@dataclass(frozen=True)
class UIConfig:
    groups: Mapping[str, Mapping[str, Sequence[str]]]


@dataclass(frozen=True)
class ScheduleDatabaseConfig:
    user: str
    password: str
    host: str
    port: int
    name: str


@dataclass(frozen=True)
class LocalDatabaseConfig:
    file: Path
    init_script: Path | None


@dataclass(frozen=True)
class Config:
    misc: MiscellaneousConfig
    bot: BotConfig
    schedule: ScheduleConfig
    schedule_database: ScheduleDatabaseConfig
    local_database: LocalDatabaseConfig
    render: ScheduleDayRenderConfig
    ui: UIConfig


def _load_miscellaneous_config(toml: Mapping) -> MiscellaneousConfig:
    event_timeout_seconds = toml["miscellaneous"]["event-timeout-seconds"]

    return MiscellaneousConfig(
        event_timeout=TimeDelta(seconds=event_timeout_seconds),
    )


def _load_schedule_day_render_config(toml: Mapping) -> ScheduleDayRenderConfig:
    return ScheduleDayRenderConfig(
        border_width=toml["render"]["border-width"],
        background_color=toml["render"]["background-color"],
        border_color=toml["render"]["border-color"],
        text_color=toml["render"]["text-color"],
        font_path=Path(toml["render"]["font-path"]),
        font_size=toml["render"]["font-size"],
        font_size_big=toml["render"]["font-size-big"],
        text_spacing=toml["render"]["text-spacing"],
        left_column_width=toml["render"]["left-column-width"],
        right_column_width=toml["render"]["right-column-width"],
        header_height=toml["render"]["header-height"],
        main_height=toml["render"]["main-height"],
        text_line_max_width=toml["render"]["text-line-max-width"],
        day_off_text=toml["render"]["day-off-text"],
        day_vacations_text=toml["render"]["day-vacations-text"],
        day_no_data_text=toml["render"]["day-no-data-text"],
    )


def _load_ui_config(toml: Mapping) -> UIConfig:
    groups: dict[str, dict[str, list[str]]] = {}

    for row in toml["user-interface"]["groups"]:
        year = row["year"]
        group = row["group"]
        subgroup = row["subgroup"]

        if year not in groups:
            groups[year] = {}

        if group not in groups[year]:
            groups[year][group] = []

        if subgroup not in groups[year][group]:
            groups[year][group].append(subgroup)

    return UIConfig(groups=groups)


def load_config() -> Config:
    load_dotenv()

    try:
        bot_token: str = getenv_str("BOT_TOKEN", required=True)

        config_file_path: str = getenv_str("CONFIG_FILE", required=True)

        # Schedule database config
        schedule_db_user: str = getenv_str("SCHEDULE_DB_USER", required=True)
        schedule_db_password: str = getenv_str(
            "SCHEDULE_DB_PASSWORD",
            required=True,
        )
        schedule_db_host: str = getenv_str("SCHEDULE_DB_HOST", required=True)
        schedule_db_port: int = getenv_int("SCHEDULE_DB_PORT", required=True)
        schedule_db_name: str = getenv_str("SCHEDULE_DB_NAME", required=True)

        # Local database config
        _local_db_file: str = getenv_str("LOCAL_DB_FILE", required=True)
        local_db_file = Path(_local_db_file)

        _local_db_init_script: str | None = getenv_str(
            "LOCAL_DB_INIT_SCRIPT",
            required=False,
        )
        if _local_db_init_script is None:
            local_db_init_script = None
        else:
            local_db_init_script = Path(_local_db_init_script)

    except ValueError as e:
        logger.info(f"Loading config failed with {e!r}")
        logger.debug(traceback.format_exc())
        raise

    with Path(config_file_path).open("rb") as file:
        config = tomllib.load(file)

    return Config(
        misc=_load_miscellaneous_config(config),
        bot=BotConfig(token=bot_token),
        schedule=ScheduleConfig(display_url=config["schedule"]["display-url"]),
        schedule_database=ScheduleDatabaseConfig(
            user=schedule_db_user,
            password=schedule_db_password,
            host=schedule_db_host,
            port=schedule_db_port,
            name=schedule_db_name,
        ),
        local_database=LocalDatabaseConfig(
            file=local_db_file,
            init_script=local_db_init_script,
        ),
        render=_load_schedule_day_render_config(config),
        ui=_load_ui_config(config),
    )
