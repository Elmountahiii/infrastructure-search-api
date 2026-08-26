import logging
import sys


LOG_FORMAT = (
    "time=%(asctime)s "
    "level=%(levelname)s "
    "logger=%(name)s "
    "%(message)s"
)


def configure_logging() -> None:
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    for logger_name, level in (
        ("app", logging.INFO),
        ("pypdf", logging.WARNING),
    ):
        configured_logger = logging.getLogger(logger_name)

        if not configured_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            configured_logger.addHandler(handler)

        configured_logger.setLevel(level)
        configured_logger.propagate = False
