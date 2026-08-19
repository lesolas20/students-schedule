from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from students_schedule.schedule import ScheduleDay


class Database:
    def __init__(self) -> None:
        ...

    def save_schedule_days(
        self,
        schedule_days: Iterable[ScheduleDay],
        *,
        overlay: bool = False,
    ) -> None:
        ...
