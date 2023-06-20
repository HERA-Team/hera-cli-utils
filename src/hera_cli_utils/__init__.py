"""Useful helper functions and argparsers for scripts.

This package contains functions that add groups of arguments to an
:class:`argparse.ArgumentParser`.
For instance, it adds a group of arguments that determine how logging proceeds, and
also a group of arguments that determine if line-profiling is run, and how.

What This Module Adds to the Logging Experience
===============================================
See the :func:`setup_logger` function for details on what is added to the logger by
this module. Note that this function must be called for logging to be altered at all
(see the "how to use" section below for details).

Note that logging in python is only used if you actually use the ``logging`` module
and make logging statements. To get the most out of this, do the following in your
modules::

    import logging
    logger = logging.getLogger(__name__)

Then, in the body of the module, add logging statements instead of standard ``print``
statements::

    logger.info("This is an informative message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")

By setting the ``--log-level`` argument to a script (that is set up according to the
guidelines in this module), you can control how much actually is printed out on any
given run. Furthermore, the logged messages include extra information, such as the
current time, the log level of the message, and optionally other info. For example,
this module adds the ability to have a column with the current and peak memory usage.
Thus, for example, instead of simply having a message that prints out as::

    This is an informative message
    This is a warning message

You get::

    00:00:54 INFO     01.650 MB | 04.402 MB This is an informative message
    00:00:55 WARNING  01.650 MB | 04.402 MB This is a warning message

The memory-printing feature is useful for a cheap way to see if a script is leaking
memory, and understanding how much memory scripts are consuming.

What This Module Does for Line-Profiling
========================================
Line-profiling is a way to see how much time is spent in each line of code. This is
useful for identifying bottlenecks in code. This module adds the ability to run a
script with line-profiling, and to save the results to a human-readable file.
Importantly, it also adds the ability to specify from the command line which functions
are included in the line-profilng. See :func:`run_with_profiling` for details.


How To Use This Module In Your Script
=====================================
This module is intended to be imported into scripts that use argparse. For instance,
say you have written a script called ``script.py``, with the following contents::

    import argparse

    # An argument parser for the script. Could be constructed from an imported function.
    parser = argparse.ArgumentParser()
    parser.add_argument("foo", type=int)

    # A function intended to do the work. Usually in hera_cal this is some imported
    # function like ``load_delay_filter_and_write``
    def run_script(**kwargs):
        print(kwargs)

    # Parse arguments and run the script
    if __name__ == "__main__":
        args = parser.parse_args()
        kwargs = var(args)
        run_script(**kwargs)

You can add better logging options and line-profiling options to this script simply by
applying ``parse_args`` to the ``args``, and running the main function through the
``run_with_profiling`` function::

    import argparse
    from hera_cli_utils import parse_args, run_with_profiling, filter_kwargs

    # An argument parser for the script. Could be constructed from an imported function.
    parser = argparse.ArgumentParser()
    parser.add_argument("foo", type=int)

    # A function intended to do the work. Usually in hera_cal this is some imported
    # function like ``load_delay_filter_and_write``
    def run_script(**kwargs):
        print(kwargs)

    # Parse arguments and run the script
    if __name__ == "__main__":
        args = parse_args(parser)         # Adds the logging/profiling arguments
        kwargs = filter_kwargs(var(args)) # Filters out the logging/profiling arguments
        run_with_profiling(run_script, args, **kwargs)  # Runs the script with profiling


How to Use This Module Interactively
====================================
This module is generally meant to be used directly in scripts, but you may want to use
some of the logging features in an interactive session. To do this, simply import
``setup_logger`` from this module, and call it::

    >>> from hera_cli_utils import setup_logger
    >>> setup_logger(level="DEBUG", show_time_as_diff=True)

Then, any logging statements in hera_cal code (or your own code in the interactive
session) will have the desired logging behavior.
"""
from __future__ import annotations

from argparse import ArgumentParser

from .logging import add_logging_args
from .logging import init_logger_from_args
from .logging import setup_logger  # noqa: F401
from .profiling import add_profiling_args
from .profiling import run_with_profiling  # noqa: F401


def parse_args(parser: ArgumentParser, args: list[str] | None = None):
    """Convenience function for setting up CLI goodies from this module.

    This function adds both profiling and logging arguments to the parser, parses the
    args, and sets up the logger. It returns the parsed args.
    """
    add_profiling_args(parser)
    add_logging_args(parser)
    args = parser.parse_args(args)
    init_logger_from_args(args)
    return args
