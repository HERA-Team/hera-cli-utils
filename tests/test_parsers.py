"""Test the parse_args function."""

from argparse import ArgumentParser

from hera_cli_utils import parse_args


def test_parse_args():
    """Test that calling parse_args works."""
    parser = ArgumentParser()
    parser.add_argument("foo", type=int)

    args = parse_args(parser, ["2"])

    assert args.foo == 2
    assert args.profile is False
    assert args.profile_funcs == ""
