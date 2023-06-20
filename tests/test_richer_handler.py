"""Tests of the RicherHandler class."""
import logging

import pytest
from pytest import LogCaptureFixture

from hera_cli_utils import RicherHandler


class TestRicherHandler:
    """Tests of the RicherHandler class."""

    def get_logger(self, **kwargs) -> logging.Logger:
        """Get a logger with INFO level."""
        logger = logging.getLogger("this")
        logger.setLevel("INFO")
        logger.addHandler(RicherHandler(**kwargs))
        return logger

    def test_no_args(self, caplog: LogCaptureFixture) -> None:
        """Test a logger with no args."""
        logger = self.get_logger()
        caplog.set_level("INFO", logger="this")
        logger.info("foo")

        assert "foo" in caplog.text

    def test_psutil(self, caplog: LogCaptureFixture) -> None:
        """Test a psutil-backend."""
        logger = self.get_logger(mem_backend="psutil")
        caplog.set_level("INFO", logger="this")
        logger.info("foo")
        assert "foo" in caplog.text

    def test_bad_mem_backend(self) -> None:
        """Test trying to set a bad memory backend."""
        with pytest.raises(ValueError, match="Invalid memory backend"):
            RicherHandler(mem_backend="bad")

    def test_not_show_time(self, caplog: LogCaptureFixture):
        """Test not rendering time."""
        logger = logging.getLogger("this")
        caplog.set_level("INFO", logger="this")
        logger.setLevel("INFO")

        logger.addHandler(RicherHandler(mem_backend="psutil"))
