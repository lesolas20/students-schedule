import logging
from typing import TYPE_CHECKING

import psycopg
from psycopg.types.json import Jsonb

if TYPE_CHECKING:
    from collections.abc import Mapping, Iterable, Sequence

    from students_schedule.schedule import ScheduleDay


logger = logging.getLogger(__name__)

logging.getLogger("psycopg").setLevel(logging.DEBUG)


class Database:
    def __init__(
        self,
        user: str,
        password: str,
        host: str,
        port: int = 5432,
        dbname: str = "postgres",
    ) -> None:
        userspec = f"{user}:{password}"
        hostspec = f"{host}:{port}"
        _dbname = f"/{dbname}"

        self.connection_uri = f"postgresql://{userspec}@{hostspec}{_dbname}"

    def save_schedule_days(
        self,
        schedule_days: Iterable[ScheduleDay],
        *,
        overlay: bool = False,
    ) -> None:
        _length = len(tuple(schedule_days))
        logger.info(f"Writing {_length} schedule days to the database")

        query = (
            "INSERT INTO schedule (schedule, overlay)"
            " VALUES (%(schedule)s, %(overlay)s)"
        )

        full_params: Sequence[Mapping] = [
            {"schedule": Jsonb(day.to_json()), "overlay": overlay}
            for day in schedule_days
        ]
        connection = psycopg.Connection.connect(self.connection_uri)

        with connection:  # noqa: SIM117
            with connection.cursor() as cursor:
                cursor.executemany(query, full_params)
