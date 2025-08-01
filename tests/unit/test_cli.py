"""Unit tests for CLI framework - PoC 1."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from agentic.cli import main


class TestCLIFramework:
    """Test the core CLI framework functionality."""

    def test_cli_help_shows_available_commands(self) -> None:
        """Test that --help shows all available commands."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "init" in result.output
        assert "generate" in result.output
        assert "review" in result.output
        assert "apply" in result.output
        assert "config" in result.output

    def test_cli_init_creates_config_file(self, temp_dir: Path) -> None:
        """Test that init command creates .agentic/config.yaml with defaults."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init"])
            
            assert result.exit_code == 0
            assert "Initialized agentic project" in result.output
            
            # Check the config file was created in the current directory
            config_file = Path(".agentic/config.yaml")
            assert config_file.exists()
            
            config_content = config_file.read_text()
            assert "llm_provider:" in config_content
            assert "sandbox_enabled: true" in config_content

    def test_cli_init_with_template_option(self, temp_dir: Path) -> None:
        """Test that init command accepts template parameter."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init", "--template", "python"])
            
            assert result.exit_code == 0
            assert "python template" in result.output.lower()

    def test_cli_generate_requires_task_description(self) -> None:
        """Test that generate command fails without task description."""
        runner = CliRunner()
        result = runner.invoke(main, ["generate"])
        
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output

    def test_cli_generate_accepts_task_description(self, temp_dir: Path) -> None:
        """Test that generate command accepts task description."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # First initialize the project
            runner.invoke(main, ["init"])
            
            # Then try to generate
            result = runner.invoke(main, ["generate", "Create a hello world function"])
            
            # Should not fail due to missing arguments
            # (May fail for other reasons like missing LLM config, but that's OK)
            assert "Missing argument" not in result.output

    def test_cli_config_get_returns_current_values(self, temp_dir: Path) -> None:
        """Test that config get returns configured values or defaults."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Initialize project first
            runner.invoke(main, ["init"])
            
            # Get a config value
            result = runner.invoke(main, ["config", "get", "sandbox_enabled"])
            
            assert result.exit_code == 0
            assert "true" in result.output.lower()

    def test_cli_config_set_updates_values(self, temp_dir: Path) -> None:
        """Test that config set updates configuration values."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Initialize project first
            runner.invoke(main, ["init"])
            
            # Set a config value
            result = runner.invoke(main, ["config", "set", "log_level", "DEBUG"])
            
            assert result.exit_code == 0
            assert "log_level" in result.output
            assert "DEBUG" in result.output

    def test_cli_shows_helpful_error_for_invalid_command(self) -> None:
        """Test that invalid commands show helpful error messages."""
        runner = CliRunner()
        result = runner.invoke(main, ["invalid-command"])
        
        assert result.exit_code != 0
        # Should suggest similar commands or show help
        assert ("No such command" in result.output or 
                "Usage:" in result.output or
                "Try" in result.output)

    def test_cli_version_flag_shows_version(self) -> None:
        """Test that --version flag shows current version."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output