"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test isolation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_project_dir(temp_dir: Path) -> Path:
    """Create a sample project structure for testing."""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir()
    
    # Create basic Python project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "README.md").write_text("# Sample Project")
    (project_dir / "pyproject.toml").write_text("""
[tool.poetry]
name = "sample-project"
version = "0.1.0"
""")
    
    return project_dir


@pytest.fixture
def agentic_config_dir(temp_dir: Path) -> Path:
    """Create .agentic directory structure for testing."""
    agentic_dir = temp_dir / ".agentic"
    agentic_dir.mkdir()
    (agentic_dir / "preview").mkdir()
    (agentic_dir / "config.yaml").write_text("""
llm_provider: "mock"
sandbox_enabled: true
log_level: "INFO"
""")
    
    return agentic_dir