"""Tests of the profiling module."""
from argparse import ArgumentParser

from hera_cli_utils import profiling as pf


parser = ArgumentParser()
parser.add_argument("foo", type=int)

pf.add_profiling_args(parser)


def some_silly_func(foo):
    """A mock function to test the profiling."""
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
