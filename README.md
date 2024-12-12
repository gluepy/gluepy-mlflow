# gluepy-mlflow

Gluepy MLOps Backend class that integrate with MLFlow.

## Get Started

```bash
pip install gluepy-mlflow
```

## Installation

```python

# Gluepy settings.py file
# Add gluepy_mlflow to the INSTALLED_MODULES list
INSTALLED_MODULES = ["gluepy_mlflow"]

# Set the MLOPS_BACKEND to gluepy_mlflow.backend.MLFlowBackend
MLOPS_BACKEND = "gluepy_mlflow.backend.MLFlowBackend"

```

## Features

- MLFlow experiment tracking integration
- Automatic system metrics logging
- Support for multiple data types (pandas DataFrame, numpy array, Spark DataFrame)
- Git-aware experiment tracking with automatic user detection
- Command-line interface for MLFlow server management from Gluepy CLI

## Requirements

- Python >=3.8
- gluepy >=1.3.0
- mlflow >=2.9.0

### Optional Dependencies

For system metrics logging:
- psutil (install with `pip install psutil`)

## Usage

### Starting MLFlow Server

Start the MLFlow tracking server using the provided CLI command:

```bash
./manage.py gluepy-mlflow runserver --port 5000 --host 127.0.0.1
```
