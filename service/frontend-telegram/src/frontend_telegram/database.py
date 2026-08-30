import logging
import sqlite3
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import date as Date  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812
from contextlib import closing

import psycopg
from psycopg.types.json import Jsonb

from students_schedule import ScheduleDay

if TYPE_CHECKING:
    from os import PathLike
    from datetime import date as Date  # noqa: N812
    from collections.abc import Mapping, Sequence

    from students_schedule import Group


logger = logging.getLogger(__name__)

logging.getLogger("psycopg").setLevel(logging.DEBUG)


class ScheduleDatabase:
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

    async def load_schedule_days(
        self,
        group: Group,
        date_start: Date,
        date_end: Date,
    ) -> Sequence[ScheduleDay]:
        # PERF: optimize to make loading 30 days take <0.2 seconds

        logger.debug(
            f"Loading schedule days from database"
            f" {date_start.isoformat()}, {date_end.isoformat()}",
        )

        days: list[ScheduleDay] = []

        query = (
            "SELECT schedule FROM schedule"
            " WHERE schedule @> %(filter)s"
            " ORDER BY id DESC, overlay DESC"
            " LIMIT 1;"
        )

        connection = await psycopg.AsyncConnection.connect(self.connection_uri)

        async with connection:  # noqa: SIM117
            async with connection.cursor() as cursor:
                for delta in range((date_end - date_start).days + 1):
                    date = date_start + TimeDelta(days=delta)
                    params: Mapping = {
                        "filter": Jsonb(
                            {"date": date.isoformat(), "group": group},
                        ),
                    }

                    await cursor.execute(query, params)
                    row = await cursor.fetchone()
                    if row is not None:
                        day = ScheduleDay.from_json(row[0])
                        days.append(day)

        logger.debug(f"Loaded days: {days}")

        return days


class LocalDatabase:
    def __init__(
        self,
        file: PathLike,
        db_init_script: PathLike | None = None,
    ) -> None:
        """Open a connection to the SQLite database file `file`.
        Execute SQL from `db_init_script` if it is not `None`.
        """
        self.file = file

        if db_init_script is not None:
            self._init_database(db_init_script)

    def _connect(self, file: PathLike) -> sqlite3.Connection:
        """Connect to an SQLite database file and return a new
        `Connection` instance.
        """
        connection = sqlite3.connect(
            file,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            autocommit=False,
        )
        connection.row_factory = sqlite3.Row

        return connection

    def _init_database(self, file: PathLike) -> None:
        sql_script = Path(file).read_text()

        with closing(self._connect(self.file)) as connection:
            connection.executescript(sql_script)
            connection.commit()

    def get_user_group(self, user_id: int) -> str | None:
        with closing(self._connect(self.file)) as connection:
            cursor = connection.execute(
                'SELECT "group" FROM users WHERE id = :id',
                {"id": user_id},
            )
            result = cursor.fetchone()

        if result is None:
            return None

        return result["group"]

    def insert_or_update_user(self, user_id: int, group: str) -> None:
        """Insert a new user entry if it does not exist, update the
        existing entry otherwise."""
        with closing(self._connect(self.file)) as connection:
            connection.execute(
                'INSERT INTO users (id, "group")'
                " VALUES (:id, :group)"
                " ON CONFLICT (id)"
                ' DO UPDATE SET "group" = :group',
                {"id": user_id, "group": group},
            )
            connection.commit()

    def user_exists(self, user_id: int) -> bool:
        with closing(self._connect(self.file)) as connection:
            cursor = connection.execute(
                "SELECT * FROM users WHERE id = :id",
                {"id": user_id},
            )
            result = cursor.fetchone()

        return result is not None
