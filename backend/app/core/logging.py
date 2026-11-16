"""Structured logging: structlog events and stdlib records share one JSON pipeline.

Privacy (brief rule 8): never log audio bytes, and never log transcripts at INFO or above.
"""

import logging
import sys
from typing import TextIO

import structlog
from structlog.types import Processor


class _StdoutHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Writes to whatever `sys.stdout` is at emit time (so redirection and capture work)."""

    def __init__(self) -> None:
        logging.Handler.__init__(self)

    @property
    def stream(self) -> TextIO:
        return sys.stdout

    @stream.setter
    def stream(self, value: TextIO) -> None:  # the base class assigns it; ignore
        pass


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    shared: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    renderer: Processor = (
        structlog.dev.ConsoleRenderer()
        if fmt == "console"
        else structlog.processors.JSONRenderer(ensure_ascii=False)
    )

    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    handler = _StdoutHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.format_exc_info,
                renderer,
            ],
        )
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Uvicorn: route through the root handler; our middleware writes the access line.
    for name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = []
        uv_logger.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
