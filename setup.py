from setuptools import setup, find_packages
from pathlib import Path
import re

# Read requirements from requirements/base.txt
def read_requirements(filename: str) -> list[str]:
    requirements_file = Path(__file__).parent / 'requirements' / filename
    with open(requirements_file) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Get version from __init__.py
def get_version():
    init_file = Path(__file__).parent / 'gluepy_ui' / '__init__.py'
    with open(init_file, 'r') as f:
        version_line = [line for line in f.readlines() if line.startswith('VERSION')][0]
        return version_line.split('=')[-1].strip().strip('"\'')

# Get requirements
install_requires = read_requirements('base.txt')
version = get_version()

setup(
    name="gluepy-ui",
    version=version,
    description="UI interface for GluePy operations",
    author="Marcus Lind",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    package_data={
        'gluepy_ui': [
            'web/core/templates/*.html',
            'web/core/templates/core/*.html',
            'web/core/static/**/*',
        ],
    },
) 