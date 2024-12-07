from typing import Dict, List, Optional, Union
from datetime import datetime
from gluepy.ops.backend import BaseOpsBackend
from gluepy.conf import default_context
import json
import os
from pathlib import Path
import django
from django.conf import settings


class GluepyUIOpsBackend(BaseOpsBackend):
    """Backend interface for GluepyUI operations using Django models."""
    
    def __init__(self):
        # Initialize Django if it hasn't been initialized
        if not settings.configured:
            # Get the path to the web directory
            import sys
            from pathlib import Path
            web_dir = Path(__file__).parent / 'web'
            package_dir = Path(__file__).parent
            
            # Add both the web directory and package directory to the Python path
            sys.path.insert(0, str(web_dir))
            sys.path.insert(0, str(package_dir))
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
        
        # Import the Run model here to avoid circular imports
        from gluepy_ui.web.core.models import Run
        self.Run = Run

    def create_run(
        self,
        dag: str,
        run_id: Optional[str] = None,
        config: Optional[Dict] = None,
        username: Optional[str] = None,
    ) -> str:
        """Creates or updates a run in the Django database."""
        # Use GluePy's default context for run_id and run_folder if not provided
        if run_id is None:
            run_id = default_context.gluepy.run_id
        
        run_folder = default_context.gluepy.run_folder
        
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
        
        # Create or update the run
        run, _ = self.Run.objects.update_or_create(
            run_id=run_id,
            defaults={
                'run_folder': run_folder,
                'dag': dag,
                'config': json.dumps(config or {}),
                'username': username
            }
        )
        return run.run_id

    def get_run(self, run_id: str) -> Dict:
        """Gets the run information from the Django database."""
        try:
            run = self.Run.objects.get(run_id=run_id)
            return {
                'run_id': run.run_id,
                'run_folder': run.run_folder,
                'dag': run.dag,
                'config': json.loads(run.config),
                'username': run.username,
                'created_at': run.created_at.isoformat(),
                'updated_at': run.updated_at.isoformat()
            }
        except self.Run.DoesNotExist:
            return {}

    def list_runs(
        self,
        dag: Optional[str] = None,
        username: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Lists runs from the Django database matching the specified criteria."""
        queryset = self.Run.objects.all()
        
        if dag:
            queryset = queryset.filter(dag=dag)
        if username:
            queryset = queryset.filter(username=username)
        if start_time:
            queryset = queryset.filter(created_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(created_at__lte=end_time)

        return [
            {
                'run_id': run.run_id,
                'run_folder': run.run_folder,
                'dag': run.dag,
                'config': json.loads(run.config),
                'username': run.username,
                'created_at': run.created_at.isoformat(),
                'updated_at': run.updated_at.isoformat()
            }
            for run in queryset
        ]

    def delete_run(self, run_id: str) -> None:
        """Deletes a run from the Django database."""
        try:
            run = self.Run.objects.get(run_id=run_id)
            run.delete()
        except self.Run.DoesNotExist:
            pass

    def log_metric(
        self,
        key: str,
        value: Union[float, int],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Logs a metric for a run."""
        run_id = default_context.gluepy.run_id
        try:
            run = self.Run.objects.get(run_id=run_id)
            from gluepy_ui.web.core.models import Metric
            Metric.objects.create(
                run=run,
                key=key,
                value=float(value),
                metric_type='metric',
                timestamp=timestamp or datetime.now()
            )
        except self.Run.DoesNotExist:
            raise ValueError(f"No run found with id {run_id}")

    def log_param(
        self,
        key: str,
        value: Union[float, int, str],
    ) -> None:
        """Logs a parameter for a run."""
        run_id = default_context.gluepy.run_id
        try:
            run = self.Run.objects.get(run_id=run_id)
            from gluepy_ui.web.core.models import Metric
            Metric.objects.create(
                run=run,
                key=key,
                value=float(value) if isinstance(value, (float, int)) else 0.0,
                metric_type='param'
            )
        except self.Run.DoesNotExist:
            raise ValueError(f"No run found with id {run_id}")

    def log_artifact(
        self,
        local_path: str,
        artifact_path: Optional[str] = None,
    ) -> None:
        """Logs an artifact file for a run."""
        run_id = default_context.gluepy.run_id
        try:
            import mimetypes
            from pathlib import Path
            from django.core.files.storage import default_storage
            from django.core.files import File
            
            run = self.Run.objects.get(run_id=run_id)
            from gluepy_ui.web.core.models import Artifact
            
            local_path = Path(local_path)
            if not local_path.exists():
                raise FileNotFoundError(f"File not found: {local_path}")
            
            # Determine artifact name and path
            name = artifact_path or local_path.name
            artifact_storage_path = f"artifacts/{run_id}/{name}"
            
            # Copy file to storage using Django's default_storage
            with open(local_path, 'rb') as source_file:
                storage_path = default_storage.save(
                    artifact_storage_path,
                    File(source_file)
                )
            
            # Create artifact record
            Artifact.objects.create(
                run=run,
                name=name,
                file_path=storage_path,
                content_type=mimetypes.guess_type(local_path)[0] or 'application/octet-stream',
                size=local_path.stat().st_size
            )
        except self.Run.DoesNotExist:
            raise ValueError(f"No run found with id {run_id}")