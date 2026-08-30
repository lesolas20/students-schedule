import re
import json
import logging
import traceback
from io import BytesIO
from time import sleep
from typing import TYPE_CHECKING
from hashlib import sha256
from datetime import datetime as DateTime  # noqa: N812
from datetime import timedelta as TimeDelta  # noqa: N812
from dataclasses import dataclass

import requests
from openpyxl import load_workbook
from schedule import every, run_all, run_pending
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell

from utils import setup_logging
from fetcher.config import Config, load_config
from fetcher.database import Database
from students_schedule import (
    Class,
    DayType,
    ScheduleDay,
    ClassTimings,
)

if TYPE_CHECKING:
    from datetime import date as Date  # noqa: N812
    from collections.abc import Mapping, Iterable, Collection

    from openpyxl.cell import _CellGetValue
    from openpyxl.cell.cell import Cell
    from openpyxl.workbook.workbook import Workbook
    from openpyxl.worksheet.worksheet import Worksheet

    from students_schedule import Group, Groups


logger = logging.getLogger(__name__)


LATEST_SCHEDULE_HASH: str = ""


@dataclass(frozen=True)
class Position:
    x: int
    y: int


@dataclass(frozen=True)
class BoundingBox:
    pos0: Position
    pos1: Position

    def __contains__(self, item: Position) -> bool:
        in_x = self.pos0.x <= item.x <= self.pos1.x
        in_y = self.pos0.y <= item.y <= self.pos1.y
        return in_x and in_y


@dataclass(frozen=True)
class ScheduleColumn:
    group: str
    sheet: str
    column: int


@dataclass(frozen=True)
class RawClass:
    subject: str | None
    professor: str | None
    room: str | None
    groups: Groups | None


# Classes in a day
type RawDaySchedule = Mapping[int, RawClass]
# Days in a week
type RawWeekSchedule = Mapping[int, RawDaySchedule]
# Weeks in a repeated block
type RawWeeksSchedule = Mapping[int, RawWeekSchedule]
# Groups with their schedule blocks
type RawFullSchedule = Mapping[Group, RawWeeksSchedule]


class RawScheduleJSONEncoder(json.JSONEncoder):
    def default(self, o):  # noqa: ANN001, ANN201
        if isinstance(o, RawClass):
            return vars(o)

        return super().default(o)


def get_cell_value(cell: Cell | MergedCell) -> _CellGetValue:
    """Retrieve the value of a cell, properly handling merged cells.
    If `cell` is a `MergedCell`, the value of the top-left cell of the
    merged range is returned.
    """
    if isinstance(cell, MergedCell):
        for merged_range in cell.parent.merged_cells.ranges:  # type: ignore
            if cell.coordinate in merged_range:
                cell = cell.parent.cell(  # type: ignore
                    row=merged_range.min_row,
                    column=merged_range.min_col,
                )
                break

    return cell.value


def get_cell(
    spreadsheet: Workbook,
    area: str,
) -> Cell | MergedCell | tuple[tuple[Cell | MergedCell, ...], ...]:
    """Get cell(s) by Excel style coordinates.
    Wraps `openpyxl.worksheet.worksheet.Worksheet.__getitem__` to
    provide sheet addressing functionality in Excel format
    "Sheet Name!CellAddress", for example "'Sheet 3'!A2",
    "MySheet!B2:J5", "'Sheet 3'!F" etc.
    If no sheet name is given, the first sheet in the spreadsheet is
    assumed.
    """
    pattern = (
        r"(?P<sheet>\S+!|'.+'!|)"
        r"(?P<range>\S+:?[a-zA-Z0-9]*)"
    )

    match = re.match(pattern, area)

    if not match:
        msg = f"{area!r} is not a valid coordinate or range"
        raise IndexError(msg)

    sheet = match.group("sheet")
    area = match.group("range")

    if sheet:
        sheet = sheet.rstrip("!").strip("'")
    else:
        sheet = spreadsheet.sheetnames[0]

    return spreadsheet[sheet][area]


def calculate_dimension(sheet: Worksheet) -> BoundingBox:
    if not sheet._cells:  # noqa: SLF001
        return BoundingBox(Position(1, 1), Position(1, 1))

    rows = set()
    cols = set()

    for row, col in sheet._cells:  # noqa: SLF001
        rows.add(row)
        cols.add(col)

    return BoundingBox(
        Position(min(cols), min(rows)),
        Position(max(cols), max(rows)),
    )


def fetch(url: str | bytes) -> bytes | None:
    """Fetch data from `url` and return response content. Return `None`
    if fetching data failed.
    """
    logger.info("Fetching data...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

    except (requests.ConnectionError, requests.HTTPError) as e:
        logger.info(f"Fetching data failed with {e!r}")
        logger.debug(traceback.format_exc())
        return None

    else:
        logger.info("Fetching data is successful")
        return response.content


def _extract_schedule_columns(
    workbook: Workbook,
) -> Collection[ScheduleColumn]:
    groups: list[ScheduleColumn] = []

    logger.debug("Extracting schedule columns...")

    for sheet_name in workbook.sheetnames:
        logger.debug(f"Checking sheet {sheet_name!r}")

        bbox = calculate_dimension(workbook[sheet_name])

        cells = get_cell(workbook, f"{sheet_name}!C1:AZ1")
        assert isinstance(cells, tuple)  # noqa: S101
        cells: Iterable[Cell | MergedCell] = cells[0]

        for cell in cells:
            assert cell.column is not None  # noqa: S101
            assert cell.row is not None  # noqa: S101

            if Position(cell.column, cell.row) not in bbox:
                continue

            _pos = Position(cell.column, cell.row)
            logger.debug(f"Checking cell at {_pos} with value {cell.value!r}")

            group_name = get_cell_value(cell)
            assert isinstance(group_name, str)  # noqa: S101

            column = ScheduleColumn(group_name, sheet_name, cell.column)

            logger.debug(f"Adding a schedule column {column}")
            groups.append(column)

    logger.debug("Extracting schedule columns is successful...")

    return tuple(groups)


def _normalize_raw_class(r: RawClass) -> RawClass:
    class_type_replacements = {
        '"лекція"': "(лекція)",
        '"лек."': "(лекція)",
        '"практична"': "(практика)",
        '"практичні_"': "(практика)",
        '"лабораторна"': "(практика)",
        '"лабораторна_"': "(практика)",
        '"лабораторна_."': "(практика)",
    }

    subject = r.subject
    professor = r.professor
    room = r.room
    groups = r.groups

    if subject in {"", "---"}:
        subject = None

    if subject == "ІТ право":  # noqa: RUF001
        subject = "IT право"

    if room == "50а":  # noqa: RUF001
        room = "а.50"  # noqa: RUF001

    if subject is not None:
        for old, new in class_type_replacements.items():
            subject = subject.replace(old, new)

        # Remove repeating whitespace
        subject = re.sub(r"\s{2,}", " ", subject)

        # Move class type onto its own line
        subject = subject.replace(" (лекція)", "\nлекція")  # noqa: RUF001
        subject = subject.replace(" (практика)", "\nпрактика")  # noqa: RUF001

    return RawClass(subject, professor, room, groups)


def _extract_class(text: str) -> RawClass:
    lines = tuple(s.strip() for s in text.split("\n"))

    result: RawClass | None = None

    match len(lines):
        case 1:
            result = RawClass(lines[0], None, None, None)

        case 2:
            result = RawClass(lines[0], lines[1], None, None)

        case 3:
            m1 = re.match(r"а\.\d+", lines[2]) is not None  # noqa: RUF001
            m2 = re.match(r"\d+а", lines[2]) is not None  # noqa: RUF001

            if m1 or m2:
                result = RawClass(lines[0], lines[1], lines[2], None)

            elif ("," in lines[0]) or ("-" in lines[0]):
                groups = tuple(s.strip() for s in lines[0].split(","))
                result = RawClass(lines[1], lines[2], None, groups)

        case 4:
            groups = tuple(s.strip() for s in lines[0].split(","))
            result = RawClass(lines[1], lines[2], lines[3], groups)

    if result is None:
        logger.warning(f"Failed to extract class data from text {text!r}")
        return RawClass(None, None, None, None)

    return _normalize_raw_class(result)


def _extract_schedule(
    workbook: Workbook,
    schedule_columns: Collection[ScheduleColumn],
) -> RawFullSchedule:
    logger.debug("Extracting schedule...")

    start_row: int = 2
    end_row: int = 51

    schedule: RawFullSchedule = {}

    # Extract data for each group
    for schedule_column in schedule_columns:
        group = schedule_column.group
        sheet = schedule_column.sheet
        column = get_column_letter(schedule_column.column)

        # Get all cells in current column
        cells_range = f"{sheet}!{column}{start_row}:{column}{end_row}"
        cells = get_cell(workbook, cells_range)
        assert isinstance(cells, tuple)  # noqa: S101
        cells = tuple(row[0] for row in cells)

        weeks: RawWeeksSchedule = {}

        for i, cell in enumerate(cells):
            cell_value = get_cell_value(cell)
            if cell_value is None:
                assert cell.column is not None  # noqa: S101
                assert cell.row is not None  # noqa: S101

                _pos = Position(cell.column, cell.row)
                logger.debug(
                    f"Got an empty cell at {_pos}, assuming empty string",
                )
                cell_value = ""

            assert isinstance(cell_value, str)  # noqa: S101

            logger.debug(f"Extracted {cell} at {i=} with value {cell_value!r}")

            week_index = i % 2  # Weeks change every cell
            day_index = i // 10  # Days change every 10 cells
            class_index = (i % 10) // 2

            _data = f"day={day_index}, class={class_index}, week={week_index}"
            logger.debug(f"Setting a value at {_data}")

            if (day_index == 0) and (class_index == 0):
                logger.debug(f"Creating an empty week {week_index}")
                weeks[week_index] = {}

            if class_index == 0:
                logger.debug(f"Creating an empty day {day_index}")
                weeks[week_index][day_index] = {}

            value = _extract_class(cell_value)

            weeks[week_index][day_index][class_index] = value

        schedule[group] = weeks

    logger.debug("Extracting schedule is successful...")

    return schedule


def parse(data: bytes) -> RawFullSchedule:
    logger.info("Parsing data...")

    wb = load_workbook(BytesIO(data))

    # Find all available groups
    groups = _extract_schedule_columns(wb)

    logger.debug(f"Extracted groups: {groups}")

    # Extract schedule for each group, week (e.g. odd & even weeks), and
    # day
    schedule = _extract_schedule(wb, groups)

    _schedule = json.dumps(
        schedule,
        ensure_ascii=False,
        indent=2,
        cls=RawScheduleJSONEncoder,
    )
    logger.debug(f"Extracted schedule: {_schedule}")

    logger.info("Parsing data is successful")

    return schedule


def get_schedule_day(
    date: Date,
    group: Group,
    semester_start_date: Date,
    class_timings: Mapping[int, ClassTimings],
    schedule: RawFullSchedule,
) -> ScheduleDay:
    logger.debug(f"Getting schedule day for {group!r} at {date}")

    _ssd = semester_start_date
    _ssd_weekday = _ssd.timetuple().tm_wday
    first_week_start_date = _ssd - TimeDelta(days=_ssd_weekday)

    week: int = (date - first_week_start_date).days // 7
    week_index: int = week % 2
    weekday: int = date.timetuple().tm_wday

    if weekday not in schedule[group][week_index]:
        return ScheduleDay(date, group, (), DayType.DAY_OFF)

    day = schedule[group][week_index][weekday]

    classes = []
    for i, raw_class in day.items():
        groups = () if raw_class.groups is None else raw_class.groups
        c = Class(
            time=class_timings[i],
            subject=raw_class.subject,
            professor=raw_class.professor,
            room=raw_class.room,
            groups=groups,
        )
        classes.append(c)

    return ScheduleDay(date, group, classes)


def update(config: Config, database: Database) -> None:
    global LATEST_SCHEDULE_HASH  # noqa: PLW0603

    logger.debug(f"Schedule URL: {config.schedule.url!r}")

    data = fetch(config.schedule.url)

    if data is None:
        logger.info("Recieved no data to process, skipping this update")
        return

    schedule = parse(data)

    schedule_hash = sha256(str(schedule).encode()).hexdigest()

    if schedule_hash == LATEST_SCHEDULE_HASH:
        logger.info("Schedule has not changed, skipping this update")
        return

    LATEST_SCHEDULE_HASH = schedule_hash

    logger.info("Schedule changed, updating data")

    # Save schedule to the database
    days = []

    class_timings = {
        0: ClassTimings("08:30", "10:10", "09:15", "09:25"),
        1: ClassTimings("10:20", "12:00", "11:05", "11:15"),
        2: ClassTimings("12:10", "13:45", "12:55", "13:00"),
        3: ClassTimings("14:30", "16:10", "15:15", "15:25"),
        4: ClassTimings("16:20", "17:35", "17:05", "17:15"),
    }

    today = DateTime.now(tz=config.timezone).date()
    semester_start_date = config.schedule.semester_start_date
    start = config.schedule.schedule_day_range_start
    stop = config.schedule.schedule_day_range_end + 1

    for day_delta in range(start, stop):
        for group in schedule:
            date = today + TimeDelta(days=day_delta)

            day = get_schedule_day(
                date,
                group,
                semester_start_date,
                class_timings,
                schedule,
            )
            logger.debug(day)
            days.append(day)

    database.save_schedule_days(tuple(days))


def main() -> None:
    setup_logging(logging.DEBUG)

    config = load_config()

    logger.debug(f"Loaded config {config}")

    database = Database(
        config.database.user,
        config.database.password,
        config.database.host,
        config.database.port,
        config.database.name,
    )

    every(30).minutes.do(update, config=config, database=database)

    run_all()

    while True:
        run_pending()
        sleep(60)


if __name__ == "__main__":
    main()
