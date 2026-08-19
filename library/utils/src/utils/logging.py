import copy
import logging
from datetime import datetime

LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S.%f%:z"


class MultilineHandler(logging.Handler):
    """Override `logging.Handler` to log multiline messages over
    multiple lines.
    """

    def emit(self, record):  # noqa: ANN001, ANN201
        s = record.getMessage()

        if "\n" not in s:
            super().emit(record)

        else:
            lines = s.splitlines()
            rec = copy.copy(record)
            rec.args = None

            for line in lines:
                rec.msg = line
                super().emit(rec)


class StreamHandler(MultilineHandler, logging.StreamHandler):
    pass


class LoggingFormatter(logging.Formatter):
    """Override `logging.Formatter` to use aware datetime objects."""

    def formatTime(self, record, datefmt=None):  # noqa: ANN001, ANN201, N802
        dt = datetime.fromtimestamp(record.created).astimezone()

        if datefmt:
            return dt.strftime(datefmt)

        return dt.isoformat(timespec="milliseconds")


def setup(level: int = logging.INFO) -> None:
    """Create the root logger and set its format and log handlers.
    Set the log level for the stderr stream handler to `level`."""

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = LoggingFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=LOG_DATE_FORMAT,
    )

    stream_handler = StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
