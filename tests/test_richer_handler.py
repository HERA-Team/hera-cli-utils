"""Tests of the RicherHandler class."""

import logging
from typing import Any

import pytest
from pytest import LogCaptureFixture

from hera_cli_utils.logging import RicherHandler

try:
    from typeguard import suppress_type_checks
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def suppress_type_checks():
        """Define a dummy suppress_type_checks function when typeguard not installed."""
        yield


class TestRicherHandler:
    """Tests of the RicherHandler class."""

    def get_logger(self, name: str, **kwargs: Any) -> logging.Logger:
        """Get a logger with INFO level."""
        logger = logging.getLogger(name)
        logger.setLevel("INFO")
        logger.addHandler(RicherHandler(**kwargs))
        return logger

    def test_no_args(self, caplog: LogCaptureFixture) -> None:
        """Test a logger with no args."""
        logger = self.get_logger("noargs")
        caplog.set_level("INFO", logger="noargs")
        logger.info("foo")

        assert "foo" in caplog.text

    def test_psutil(self, caplog: LogCaptureFixture) -> None:
        """Test a psutil-backend."""
        logger = self.get_logger("psutil", mem_backend="psutil")
        caplog.set_level("INFO", logger="psutil")
        logger.warning("foo")
        assert "foo" in caplog.text

    def test_bad_mem_backend(self) -> None:
        """Test trying to set a bad memory backend."""
        with pytest.raises(ValueError, match="Invalid memory backend"):
            with suppress_type_checks():
                RicherHandler(mem_backend="bad")  # type: ignore

    def test_not_show_time(self, caplog: LogCaptureFixture) -> None:
        """Test not rendering time."""
        logger = self.get_logger("notime", show_time=False)
        caplog.set_level("INFO", logger="notime")
        logger.info("foo")
        assert "foo" in caplog.text

    def test_not_show_level(self, caplog: LogCaptureFixture) -> None:
        """Test not rendering level."""
        logger = self.get_logger("nolevel", show_level=False)
        caplog.set_level("INFO", logger="nolevel")
        logger.info("foo")
        assert "foo" in caplog.text

    def test_not_show_mem_usage(self, caplog: LogCaptureFixture) -> None:
        """Test not rendering memory usage."""
        logger = self.get_logger("nomem", show_mem_usage=False)
        caplog.set_level("INFO", logger="nomem")
        logger.info("foo")
        assert "foo" in caplog.text
