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


@dataclass(frozen=True)
class Class:
    time: ClassTimings
    subject: Subject
    professor: Professor
    room: Room
    groups: Groups


@dataclass(frozen=True)
class ScheduleDay:
    date: Date
    group: Group
    classes: Iterable[Class]
    day_type: DayType = DayType.NORMAL


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
