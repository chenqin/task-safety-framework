#!/usr/bin/env python3
"""Setup script for task-safety-framework."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read version
version = "1.0.0"

setup(
    name="task-safety-framework",
    version=version,
    author="OpenClaw Community",
    author_email="community@openclaw.ai",
    description="Checkpointing and recovery framework for long-running Python tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chenqin/task-safety-framework",
    project_urls={
        "Documentation": "https://github.com/chenqin/task-safety-framework#readme",
        "Bug Tracker": "https://github.com/chenqin/task-safety-framework/issues",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "task-recovery=task_safety_framework.task_recovery:main",
        ],
    },
)
