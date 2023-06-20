"""Module adding line-profiling functionality to a CLI."""
import importlib
import logging
import warnings
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path
from typing import Callable

from line_profiler import LineProfiler


logger = logging.getLogger(__name__)


def _add_profile_funcs(profiler, profile_funcs):
    for fnc in profile_funcs.split(","):
        module = importlib.import_module(fnc.split(":")[0])
        _fnc = module
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            if ":" not in fnc:
                profiler.add_module(_fnc)
            else:
                for att in fnc.split(":")[-1].split("."):
                    _fnc = getattr(_fnc, att)
                profiler.add_function(_fnc)


def run_with_profiling(function: Callable, args: Namespace, *posargs, **kwargs):
    """Run a function with profiling if the user has requested it.

    Only runs profiling if `args.profile` is True, and doesn't even import
    ``line_profiler`` if it's not.

    Parameters
    ----------
    function
        The function to run.
    args
        The namespace object returned by ``ArgumentParser.parse_args()``. This must
        have a ``profile`` attribute that is True if profiling is requested, as well
        as a ``profile_output`` attribute that is the path to the output file,
        and a ``profile_funcs`` attribute that is a comma-separated list of functions to
        profile. Use :func:`add_profiling_args` to add these arguments to your parser.
    posargs
        Positional arguments to pass to ``function``.
    kwargs
        Keyword arguments to pass to ``function``.
    """
    if not args.profile:
        return function(*posargs, **kwargs)
    logger.info(f"Profiling {function.__name__}. Output to {args.profile_output}")

    profiler = LineProfiler()

    profiler.add_function(function)

    # Now add any user-defined functions that they want to be profiled.
    # Functions must be sent in as "path.to.module:function_name" or
    # "path.to.module:Class.method".
    if args.profile_funcs:
        _add_profile_funcs(profiler, args.profile_funcs)

    pth = Path(args.profile_output)
    if not pth.parent.exists():
        pth.parent.mkdir(parents=True)

    out = profiler.runcall(function, *posargs, **kwargs)

    with open(pth, "w") as fl:
        profiler.print_stats(stream=fl, stripzeros=True)

    return out


def add_profiling_args(parser: ArgumentParser):
    """Add profiling arguments to an argparse parser.

    All arguments are optional and have sensible defaults. All arguments begin with
    "profile-" so they can be easily identified.
    """
    grp = parser.add_argument_group(title="Options for line-profiling")

    grp.add_argument("--profile", action="store_true", help="Line-Profile the script")
    grp.add_argument(
        "--profile-funcs", type=str, default="", help="List of functions to profile"
    )
    grp.add_argument(
        "--profile-output", type=str, help="Output file for profiling info."
    )
