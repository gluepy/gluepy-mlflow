from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from gluepy.ops.backend import BaseOpsBackend
from gluepy.conf import default_context
import json
import os
from pathlib import Path


class MLFlowBackend(BaseOpsBackend):
    """Backend interface for MLFlow operations."""
    
    def __init__(self):
        try:
            import mlflow
        except ImportError as exc:
            raise ImportError(
                "Couldn't import MLFlow. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
        self.mlflow = mlflow

    def create_run(
        self,
        dag: str,
        run_id: Optional[str] = None,
        config: Optional[Dict] = None,
        username: Optional[str] = None,
    ) -> str:
        """Creates a new run in MLFlow."""
        # Use GluePy's default context for run_id if not provided
        if run_id is None:
            run_id = default_context.gluepy.run_id

        # Try to get username if not provided
        if username is None:
            # Try git config user.name
            try:
                import subprocess
                git_username = subprocess.check_output(
                    ['git', 'config', 'user.name'],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8').strip()
                username = git_username
            except (subprocess.SubprocessError, FileNotFoundError):
                # Try environment username
                try:
                    import getpass
                    env_username = getpass.getuser()
                    username = env_username
                except Exception:
                    username = "AnonymousUser"

        # Create tags dictionary with run_id included
        tags = {
            "dag": dag,
            "username": username,
            "run_folder": default_context.gluepy.run_folder,
            "gluepy.run_id": run_id    # Store our run_id as a tag
        }

        # Get or create experiment by DAG name
        try:
            experiment = self.mlflow.get_experiment_by_name(dag)
            if experiment is None:
                experiment_id = self.mlflow.create_experiment(dag)
            else:
                experiment_id = experiment.experiment_id
        except self.mlflow.exceptions.MlflowException:
            experiment_id = self.mlflow.create_experiment(dag)

        # Enable system metrics if psutil is installed
        try:
            import psutil
            self.mlflow.enable_system_metrics_logging()
        except ImportError:
            pass

        # Create new run
        run = self.mlflow.start_run(
            experiment_id=experiment_id,
            run_name=run_id,
            tags=tags,
        )

        # Log config as parameters if provided
        if config:
            self.log_param_dict(config)

        return run.info.run_id

    def log_param_dict(self, param_dict: Dict[str, Any], prefix: Optional[str] = None) -> None:
        """Logs a dictionary of parameters to MLFlow."""
        for key, value in param_dict.items():
            key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (str, int, float, bool)):
                self.log_param(key, value)
            elif isinstance(value, datetime):
                self.log_param(key, value.isoformat())
            elif isinstance(value, dict):
                self.log_param_dict(value, prefix=key)
            else:
                # For complex types, store as JSON string
                self.log_param(key, json.dumps(value))

    def get_run(self, run_id: str) -> Dict:
        """Gets the run information from MLFlow."""
        try:
            run = self.mlflow.get_run(run_id)
            return {
                'run_id': run.info.run_id,
                'run_folder': run.data.tags.get('run_folder', ''),
                'dag': run.data.tags.get('dag', ''),
                'config': run.data.params,
                'username': run.data.tags.get('username', ''),
                'created_at': run.info.start_time,
                'updated_at': run.info.end_time or run.info.start_time
            }
        except self.mlflow.exceptions.MlflowException:
            return {}

    def list_runs(
        self,
        dag: Optional[str] = None,
        username: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Lists runs from MLFlow matching the specified criteria."""
        # Construct filter string
        filter_string = []
        if dag:
            filter_string.append(f"tags.dag = '{dag}'")
        if username:
            filter_string.append(f"tags.username = '{username}'")
        if start_time:
            filter_string.append(f"start_time >= {int(start_time.timestamp() * 1000)}")
        if end_time:
            filter_string.append(f"start_time <= {int(end_time.timestamp() * 1000)}")

        # Get runs from MLFlow
        runs = self.mlflow.search_runs(
            filter_string=" and ".join(filter_string) if filter_string else "",
            output_format="list"
        )

        return [
            {
                'run_id': run.info.run_id,
                'run_folder': run.data.tags.get('run_folder', ''),
                'dag': run.data.tags.get('dag', ''),
                'config': run.data.params,
                'username': run.data.tags.get('username', ''),
                'created_at': run.info.start_time,
                'updated_at': run.info.end_time or run.info.start_time
            }
            for run in runs
        ]

    def delete_run(self, run_id: str) -> None:
        """Deletes a run from MLFlow."""
        try:
            self.mlflow.delete_run(run_id)
        except self.mlflow.exceptions.MlflowException:
            pass

    def log_metric(
        self,
        key: str,
        value: Union[float, int],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Logs a metric to MLFlow."""
        timestamp_ms = int(timestamp.timestamp() * 1000) if timestamp else None
        self.mlflow.log_metric(
            key=key,
            value=float(value),
            timestamp=timestamp_ms
        )

    def log_param(
        self,
        key: str,
        value: Union[float, int, str],
    ) -> None:
        """Logs a parameter to MLFlow."""
        if isinstance(value, (float, int)):
            self.mlflow.log_param(key, float(value))
        else:
            self.mlflow.log_param(key, str(value))

    def log_artifact(
        self,
        local_path: str,
        artifact_path: Optional[str] = None,
    ) -> None:
        """Logs an artifact file to MLFlow."""
        self.mlflow.log_artifact(
            local_path=local_path,
            artifact_path=artifact_path
        )

    def log_input(
        self,
        df: Any,
        context: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ) -> None:
        """Logs an input dataset to MLFlow.
        
        Args:
            df: Input dataset (pandas DataFrame, numpy array, spark DataFrame, etc.)
            context: Optional context string (e.g., 'training', 'validation')
            tags: Optional dictionary of tags to associate with the dataset
        """
        # Import necessary converters
        from mlflow.data.pandas_dataset import from_pandas
        from mlflow.data.numpy_dataset import from_numpy
        try:
            from mlflow.data.spark_dataset import from_spark
            SPARK_AVAILABLE = True
        except ImportError:
            SPARK_AVAILABLE = False

        # Determine the type of dataset and convert accordingly
        dataset = None
        
        # Check if it's a pandas DataFrame
        if 'pandas' in str(type(df)):
            import pandas as pd
            if isinstance(df, pd.DataFrame):
                dataset = from_pandas(df, *args, **kwargs)
        
        # Check if it's a numpy array
        elif 'numpy' in str(type(df)):
            import numpy as np
            if isinstance(df, np.ndarray):
                dataset = from_numpy(df, *args, **kwargs)
        
        # Check if it's a Spark DataFrame (if Spark is available)
        elif SPARK_AVAILABLE and 'pyspark' in str(type(df)):
            if hasattr(df, 'rdd'):  # Basic check for Spark DataFrame
                dataset = from_spark(df, *args, **kwargs)
        
        if dataset is None:
            raise ValueError(
                f"Unsupported dataset type: {type(df)}. "
                "Supported types are: pandas DataFrame, numpy array, "
                "and Spark DataFrame (if available)."
            )

        # Log the dataset as input
        self.mlflow.log_input(
            dataset=dataset,
            context=context,
            tags=tags
        )
