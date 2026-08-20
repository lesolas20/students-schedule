from enum import Enum
from typing import TYPE_CHECKING
from dataclasses import dataclass
from collections.abc import Collection

if TYPE_CHECKING:
    from datetime import date as Date  # noqa: N812
    from collections.abc import Iterable


type Time = str
type Group = str
type Subject = str | None
type Professor = str | None
type Room = str | None
type Groups = Collection[Group]


class DayType(Enum):
    NORMAL = 0
    DAY_OFF = 1
    EXAM = 2


@dataclass(frozen=True)
class ClassTimings:
    class_start: Time
    class_end: Time
    break_start: Time
    break_end: Time

    def to_json(self) -> dict:
        return {
            "class_start": self.class_start,
            "class_end": self.class_end,
            "break_start": self.break_start,
            "break_end": self.break_end,
        }


@dataclass(frozen=True)
class Class:
    time: ClassTimings
    subject: Subject
    professor: Professor
    room: Room
    groups: Groups

    def to_json(self) -> dict:
        return {
            "time": self.time.to_json(),
            "subject": self.subject,
            "professor": self.professor,
            "room": self.room,
            "groups": self.groups,
        }


@dataclass(frozen=True)
class ScheduleDay:
    date: Date
    group: Group
    classes: Iterable[Class]
    day_type: DayType = DayType.NORMAL

    def to_json(self) -> dict:
        date: str = self.date.strftime("%Y-%m-%d")
        group: str = self.group
        classes: list = [c.to_json() for c in self.classes]
        day_type: int = self.day_type.value

        return {
            "date": date,
            "group": group,
            "class": classes,
            "day_type": day_type,
        }


@dataclass(frozen=True)
class ScheduleWeek:
    date_start: Date
    date_end: Date
    days: Iterable[ScheduleDay]


@dataclass(frozen=True)
class ScheduleMonth:
    date_start: Date
    date_end: Date
    days: Iterable[ScheduleDay]
