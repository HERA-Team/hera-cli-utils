"""HERA CLI Utils.

Useful helper functions and argparsers for running HERA CLI scripts.
"""
from __future__ import annotations

import math
import tracemalloc as tr
from collections.abc import Iterable
from datetime import datetime, timedelta
from string import Template
from typing import Literal, Any

from rich._log_render import FormatTimeCallable
from rich.console import Console
from rich.console import ConsoleRenderable
from rich.containers import Renderables
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich.text import TextType


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
        rich_log_render: LogRender,
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

    def render_time(self, console: Console, log_time: datetime | None=None, time_format: str | Text | FormatTimeCallable | None =None) -> str | Text:
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
