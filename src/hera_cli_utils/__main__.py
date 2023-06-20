"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """HERA CLI Utils."""


if __name__ == "__main__":
    main(prog_name="hcu")  # pragma: no cover
