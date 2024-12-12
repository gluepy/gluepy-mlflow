import click
from gluepy.commands import cli
import os
import sys
from pathlib import Path


@cli.group()
def gluepy_mlflow():
    """GluePy UI management commands."""
    pass


@gluepy_mlflow.command()
@click.option('--port', '-p', default=5000, help='Port to run the MLFlow server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to run the MLFlow server on')
@click.option('--backend-store-uri', default='sqlite:///mlflow.db', help='Database URI for MLFlow tracking')
@click.option('--default-artifact-root', default='./mlruns', help='Local or S3 URI to store artifacts')
def runserver(port, host, backend_store_uri, default_artifact_root):
    """
    Start the MLFlow tracking server.

    This command runs the MLFlow tracking server for experiment tracking.
    By default, it runs on http://127.0.0.1:5000/
    """
    try:
        from mlflow.server import _run_server
    except ImportError as exc:
        raise ImportError(
            "Couldn't import MLFlow. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Create the artifact store directory if it doesn't exist
    if default_artifact_root.startswith('./'):
        Path(default_artifact_root).mkdir(parents=True, exist_ok=True)

    # Run the MLFlow server with correct parameters
    _run_server(
        file_store_path=default_artifact_root,
        registry_store_uri=backend_store_uri,
        default_artifact_root=default_artifact_root,
        serve_artifacts=True,
        artifacts_only=False,
        artifacts_destination=None,
        host=host,
        port=port,
        static_prefix="",
        workers=1,
        gunicorn_opts=None,
        waitress_opts=None,
        expose_prometheus=None,
        app_name=None
    )
