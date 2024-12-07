import click
from gluepy.commands import cli


@cli.command()
def sample():
    """
    Sample command generated.

    Can be called using ./manage.py sample
    """
    click.echo("Sample command called")