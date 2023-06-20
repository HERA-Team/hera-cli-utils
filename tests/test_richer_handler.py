
import logging
from hera_cli_utils import RicherHandler
import pytest
from pytest.logging import LogCaptureFixture

class TestRicherHandler:
    def get_logger(self, **kwargs) -> logging.Logger:
        logger = logging.getLogger("this")
        logger.setLevel("INFO")
        logger.addHandler(RicherHandler(**kwargs))
        return logger

    def test_no_args(self, caplog: LogCaptureFixture) -> None:
        logger = self.get_logger()
        caplog.set_level("INFO", logger="this")
        logger.info("foo")

        assert "foo" in caplog.text

    def test_psutil(self, caplog: LogCaptureFixture) -> None:
        logger = self.get_logger(mem_backend="psutil")
        caplog.set_level("INFO", logger="this")
        logger.info("foo")
        assert "foo" in caplog.text

    def test_bad_mem_backend(self) -> None:
        with pytest.raises(ValueError, match="Invalid memory backend"):
            RicherHandler(mem_backend="bad")

    def test_not_show_time(self, caplog: LogCaptureFixture):
        logger = logging.getLogger("this")
        caplog.set_level("INFO", logger="this")
        logger.setLevel("INFO")

        logger.addHandler(RicherHandler(mem_backend="psutil"))
