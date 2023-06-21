"""Module for adding a nicer logger and ability to turn it on in a CLI."""

from __future__ import annotations

import logging
import math
import tracemalloc as tr
from argparse import ArgumentParser
from collections.abc import Iterable
from datetime import datetime
from datetime import timedelta
from string import Template
from typing import Any
from typing import Literal

from rich._log_render import FormatTimeCallable
from rich._log_render import LogRender as RichLogRender
from rich.console import Console
from rich.console import ConsoleRenderable
from rich.containers import Renderables
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich.text import TextType


logger = logging.getLogger(__name__)


class DeltaTemplate(Template):
    """Custom string template for formatting timedelta objects."""

    delimiter = "%"


def strfdelta(tdelta: timedelta, fmt: str) -> str:
    """Format a timedelta object as a string."""
    days = tdelta.days
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d = {
        "D": f"{days:02d}",
        "H": f"{hours + 24*days:02d}",
        "h": f"{hours:02d}",
        "M": f"{minutes:02d}",
        "S": f"{seconds:02d}",
    }

    t = DeltaTemplate(fmt)
    return t.substitute(**d)


def fmt_bytes(x: float | int) -> str:
    """Format a number in bytes."""
    order = int(math.log(x, 1024))
    x /= 1024**order

    if x >= 100.0:
        order += 1
        x /= 1024

    unit = [" B", "KB", "MB", "GB", "TB"][order]
    return f"{x:06.3f} {unit}"


class LogRender:
    """Custom log render for rich logging.

    This is typically not instantiated directly, but through the :class:`RicherHandler`
    class.
    """

    def __init__(
        self,
        show_time: bool = True,
        show_level: bool = False,
        show_path: bool = True,
        time_format: str | FormatTimeCallable = "[%x %X]",
        omit_repeated_times: bool = True,
        level_width: int | None = 8,
        show_mem_usage: bool = True,
        mem_backend: Literal["tracemalloc", "psutil"] = "tracemalloc",
        show_time_as_diff: bool = False,
        delta_time_format: str = "%H:%M:%S",
    ) -> None:
        """Initialize a LogRender instance.

        Parameters
        ----------
        show_time
            Whether to show the time in the log output.
        show_level
            Whether to show the log level in the log output.
        show_path
            Whether to show the path to the log message in the log output.
        time_format
            The format to use for the time.
        omit_repeated_times
            Whether to omit repeated times in the log output.
        level_width
            The width of the log level column in units of characters.
        show_mem_usage
            Whether to show memory usage in the log output.
        mem_backend
            The memory backend to use. Either "tracemalloc" or "psutil".
        show_time_as_diff
            Whether to show the time as a difference from the first log message.
        delta_time_format
            The format to use for the time difference.
        """
        self.show_time = show_time
        self.show_level = show_level
        self.show_path = show_path
        self.time_format = time_format
        self.omit_repeated_times = omit_repeated_times
        self.level_width = level_width
        self._last_time: Text | None = None
        self._first_time: datetime | None = None
        self.delta_time_format = delta_time_format

        self.show_mem_usage = show_mem_usage
        self.mem_backend = mem_backend
        if mem_backend == "tracemalloc":
            if not tr.is_tracing():
                tr.start()

        elif mem_backend == "psutil":
            import psutil

            self._pr = psutil.Process
        else:
            raise ValueError(f"Invalid memory backend: {mem_backend}")

        self.show_time_as_diff = show_time_as_diff

    @classmethod
    def from_rich(
        cls,
        rich_log_render: RichLogRender,
        show_mem_usage: bool = True,
        mem_backend: Literal["tracemalloc", "psutil"] = "tracemalloc",
        show_time_as_diff: bool = False,
        delta_time_format: str = "%H:%M:%S",
    ) -> LogRender:
        """Create a RichLog instance from a RichLog instance.

        Parameters
        ----------
        rich_log_render
            A RichLog instance.
        show_mem_usage
            Whether to show memory usage in the log output.
        mem_backend
            The memory backend to use. Either "tracemalloc" or "psutil".
        show_time_as_diff
            Whether to show the time as a difference from the first log message.
        delta_time_format
            The format to use for the time difference.
        """
        return cls(
            show_time=rich_log_render.show_time,
            show_level=rich_log_render.show_level,
            show_path=rich_log_render.show_path,
            time_format=rich_log_render.time_format,
            omit_repeated_times=rich_log_render.omit_repeated_times,
            level_width=rich_log_render.level_width,
            show_mem_usage=show_mem_usage,
            mem_backend=mem_backend,
            show_time_as_diff=show_time_as_diff,
            delta_time_format=delta_time_format,
        )

    def __call__(
        self,
        console: Console,
        renderables: Iterable[ConsoleRenderable],
        log_time: datetime | None = None,
        time_format: str | FormatTimeCallable | None = None,
        level: TextType = "",
        path: str | None = None,
        line_no: int | None = None,
        link_path: str | None = None,
    ) -> Table:
        """Render a log message."""
        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_time:
            output.add_column(style="log.time")
        if self.show_level:
            output.add_column(style="log.level", width=self.level_width)

        if self.show_mem_usage:
            output.add_column()

        output.add_column(ratio=1, style="log.message", overflow="fold")

        if self.show_path and path:
            output.add_column(style="log.path")

        row: list[str | Text | Renderables] = []
        if self.show_time:
            row.append(self.render_time(console, log_time, time_format))

        if self.show_level:
            row.append(level)

        if self.show_mem_usage:
            row.append(self.render_mem_usage())

        row.append(Renderables(renderables))
        if self.show_path and path:
            path_text = Text()
            path_text.append(
                path, style=f"link file://{link_path}" if link_path else ""
            )
            if line_no:
                path_text.append(":")
                path_text.append(
                    f"{line_no}",
                    style=f"link file://{link_path}#{line_no}" if link_path else "",
                )
            row.append(path_text)

        output.add_row(*row)
        return output

    def render_time(
        self,
        console: Console,
        log_time: datetime | None = None,
        time_format: str | Text | FormatTimeCallable | None = None,
    ) -> str | Text:
        """Render the current time."""
        log_time = log_time or console.get_datetime()
        if self._first_time is None:
            self._first_time = log_time

        if self.show_time_as_diff:
            return strfdelta(log_time - self._first_time, self.delta_time_format)
        time_format = time_format or self.time_format
        log_time_display = (
            time_format(log_time)
            if callable(time_format)
            else Text(log_time.strftime(time_format))
        )
        if log_time_display == self._last_time and self.omit_repeated_times:
            return Text(" " * len(log_time_display))
        self._last_time = log_time_display
        return log_time_display

    def render_mem_usage(self) -> str:
        """Render the current memory usage."""
        if self.mem_backend == "psutil":
            m = self._pr().memory_info().rss
            return fmt_bytes(m)
        elif self.mem_backend == "tracemalloc":
            m, p = tr.get_traced_memory()
            return f"{fmt_bytes(m)} | {fmt_bytes(p)}"


class RicherHandler(RichHandler):
    """An extension of RichHandler that adds memory usage and time difference."""

    def __init__(
        self,
        *args: Any,
        show_mem_usage: bool = True,
        mem_backend: Literal["tracemalloc", "psutil"] = "tracemalloc",
        show_time_as_diff: bool = False,
        delta_time_format: str = "%H:%M:%S",
        **kwargs: dict[str, Any],
    ):
        """Initialize a RicherHandler.

        Parameters are the same as :class:`rich.logging.RichHandler`, with the following
        additions.

        Parameters
        ----------
        show_mem_usage
            Whether to show memory usage in the log output.
        mem_backend
            The memory backend to use. Either "tracemalloc" or "psutil".
        show_time_as_diff
            Whether to show the time as a difference from the first log message.
        delta_time_format
            The format to use for the time difference.
        """
        super().__init__(*args, **kwargs)
        self._log_render = LogRender.from_rich(
            self._log_render,
            show_mem_usage=show_mem_usage,
            mem_backend=mem_backend,
            show_time_as_diff=show_time_as_diff,
            delta_time_format=delta_time_format,
        )


logger = logging.getLogger(__name__)


def setup_logger(
    level: str = "INFO",
    width: int = 160,
    show_time_as_diff: bool = True,
    rich_tracebacks: bool = True,
    show_mem: bool = True,
    mem_backend: Literal["tracemalloc", "psutil"] = "tracemalloc",
    show_path: bool = False,
) -> None:
    """Setup a default logger for use in a script.

    Parameters
    ----------
    level : str, optional
        The logging level to use. Only messages at or above this level will be printed.
        Options are "DEBUG", "INFO", "WARNING", "ERROR", and "CRITICAL".
    width : int, optional
        The width of the on-screen text before wrapping.
    show_time_as_diff : bool, optional
        If True, show the time since the last message. If False, show the absolute time.
    rich_tracebacks : bool, optional
        If True, show tracebacks with rich formatting. If False, show tracebacks with
        plain formatting.
    show_mem : bool, optional
        If True, show the current and peak memory usage in the log messages.
    mem_backend : {"tracemalloc", "psutil"}, optional
        The backend to use for measuring memory usage. "tracemalloc" is the default, but
        "psutil" is more accurate.
    show_path : bool, optional
        If True, show the path to the file where the log message was generated on each
        log line.
    """
    cns = Console(width=width)

    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=[
            RicherHandler(
                console=cns,
                rich_tracebacks=rich_tracebacks,
                tracebacks_show_locals=True,
                show_path=show_path,
                show_time_as_diff=show_time_as_diff,
                show_mem_usage=show_mem,
                mem_backend=mem_backend,
            )
        ],
        force=True,
    )


def add_logging_args(parser: ArgumentParser):
    """Add logging arguments to an argparse parser.

    All arguments are optional and have sensible defaults. All arguments begin
    with "log-" so they can be easily identified.
    """
    grp = parser.add_argument_group(title="Options for logging")

    grp.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["INFO", "ERROR", "WARNING", "CRITICAL", "DEBUG"],
        help="logging level to display. ",
    )
    grp.add_argument(
        "--log-width", type=int, default=160, help="width of logging output"
    )
    grp.add_argument(
        "--log-plain-tracebacks",
        action="store_true",
        help="use plain instead of rich tracebacks",
    )
    grp.add_argument(
        "--log-absolute-time",
        action="store_true",
        help="show logger time as absolute instead of relative to start",
    )
    grp.add_argument(
        "--log-no-mem", action="store_true", help="do not show memory usage"
    )
    grp.add_argument(
        "--log-mem-backend",
        type=str,
        default="tracemalloc",
        choices=["tracemalloc", "psutil"],
    )
    grp.add_argument(
        "--log-show-path", action="store_true", help="show path of code in log msg"
    )


def init_logger_from_args(args):
    """Call :func:`setup_logger` with arguments from an argparse parser."""
    setup_logger(
        width=args.log_width,
        level=args.log_level,
        rich_tracebacks=not args.log_plain_tracebacks,
        show_time_as_diff=not args.log_absolute_time,
        mem_backend=args.log_mem_backend,
        show_mem=not args.log_no_mem,
        show_path=args.log_show_path,
    )
