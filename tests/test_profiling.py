"""Tests of the profiling module."""

from argparse import ArgumentParser

from hera_cli_utils import logging as lg
from hera_cli_utils import profiling as pf

parser = ArgumentParser()
parser.add_argument("foo", type=int)

pf.add_profiling_args(parser)


def some_silly_func(foo):
    """Test the profiling.

    Just a silly mock function to test profiling.
    """
    return foo


def test_run_with_profiling(tmp_path_factory):
    """Test running with profiling."""
    tmpdir = tmp_path_factory.mktemp("test_run_with_profiling")
    args = parser.parse_args(
        ["2", "--profile", "--profile-output", f"{tmpdir}/test.prof"]
    )
    pf.run_with_profiling(some_silly_func, args, 2)
    assert (tmpdir / "test.prof").exists()


def test_run_without_profiling(tmp_path_factory):
    """Test running without profiling."""
    tmpdir = tmp_path_factory.mktemp("test_run_without_profiling")
    args = parser.parse_args(["2"])
    pf.run_with_profiling(some_silly_func, args, 2)
    assert not (tmpdir / "test.prof").exists()


def test_run_with_profiling_funcs(tmp_path_factory):
    """Test running with profiling, with extra functions."""
    tmpdir = tmp_path_factory.mktemp("test_run_with_profiling_funcs")

    args = parser.parse_args(
        [
            "2",
            "--profile",
            "--profile-output",
            f"{tmpdir}/test.prof",
            "--profile-funcs",
            "hera_cli_utils.logging:fmt_bytes,hera_cli_utils.logging:LogRender",
        ]
    )
    pf.run_with_profiling(some_silly_func, args, 2)
    assert (tmpdir / "test.prof").exists()


def test_add_profile_funcs():
    """Explicitly test adding profile functions."""

    class MockProfiler:
        def __init__(self):
            self.funcs = []
            self.modules = []

        def add_function(self, func):
            self.funcs.append(func)

        def add_module(self, module):
            self.modules.append(module)

    mock_profiler = MockProfiler()

    pf._add_profile_funcs(mock_profiler, "hera_cli_utils.logging")
    assert lg in mock_profiler.modules

    pf._add_profile_funcs(mock_profiler, "hera_cli_utils.logging:fmt_bytes")
    assert lg.fmt_bytes in mock_profiler.funcs

    pf._add_profile_funcs(mock_profiler, "hera_cli_utils.logging:LogRender.__call__")
    assert lg.LogRender.__call__ in mock_profiler.funcs
