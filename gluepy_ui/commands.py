import click
from gluepy.commands import cli
import os
import sys
from pathlib import Path


@cli.group()
def gluepyui():
    """GluePy UI management commands."""
    pass


@gluepyui.command()
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to run the server on')
def runserver(port, host):
    """
    Start the Django development server.

    This command runs the Django development server for the web application.
    By default, it runs on http://127.0.0.1:8000/
    """
    # Get the path to the web directory
    web_dir = Path(__file__).parent / 'web'
    
    # Add the web directory to the Python path
    sys.path.insert(0, str(web_dir))
    
    # Change to the web directory
    os.chdir(web_dir)
    
    # Set the Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    
    try:
        from django.core.management.commands.runserver import Command as RunserverCommand
        from django.core.management import ManagementUtility
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    sys.argv = ['manage.py', 'runserver', f'{host}:{port}']
    # Initialize Django
    utility = ManagementUtility(['manage.py'])
    utility.execute()
    
    # Run the server
    server = RunserverCommand()
    server.run_from_argv(sys.argv)
