"""Unit tests for configuration management."""

from pathlib import Path

import pytest
import yaml

from agentic.config import Config, ConfigManager


class TestConfigManager:
    """Test configuration management functionality."""

    def test_config_manager_creates_default_config(self, temp_dir: Path) -> None:
        """Test that ConfigManager creates default configuration."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        config = config_manager.load()
        
        assert config.llm_provider == "openai"
        assert config.sandbox_enabled is True
        assert config.log_level == "INFO"
        assert config_dir.exists()

    def test_config_manager_loads_existing_config(self, temp_dir: Path) -> None:
        """Test that ConfigManager loads existing configuration."""
        config_dir = temp_dir / ".agentic"
        config_dir.mkdir()
        
        # Create existing config
        config_file = config_dir / "config.yaml"
        config_data = {
            "llm_provider": "anthropic",
            "sandbox_enabled": False,
            "log_level": "DEBUG"
        }
        config_file.write_text(yaml.dump(config_data))
        
        config_manager = ConfigManager(config_dir)
        config = config_manager.load()
        
        assert config.llm_provider == "anthropic"
        assert config.sandbox_enabled is False
        assert config.log_level == "DEBUG"

    def test_config_manager_saves_config(self, temp_dir: Path) -> None:
        """Test that ConfigManager saves configuration to file."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        config = Config(
            llm_provider="claude",
            sandbox_enabled=True,
            log_level="WARNING"
        )
        
        config_manager.save(config)
        
        # Verify file was created and contains correct data
        config_file = config_dir / "config.yaml"
        assert config_file.exists()
        
        loaded_data = yaml.safe_load(config_file.read_text())
        assert loaded_data["llm_provider"] == "claude"
        assert loaded_data["sandbox_enabled"] is True
        assert loaded_data["log_level"] == "WARNING"

    def test_config_get_value_returns_correct_value(self, temp_dir: Path) -> None:
        """Test that get_value returns the correct configuration value."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        # Load default config
        config = config_manager.load()
        
        assert config_manager.get_value("llm_provider") == config.llm_provider
        assert config_manager.get_value("sandbox_enabled") == config.sandbox_enabled

    def test_config_set_value_updates_and_saves(self, temp_dir: Path) -> None:
        """Test that set_value updates configuration and saves to file."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        # Load initial config
        config_manager.load()
        
        # Update a value
        config_manager.set_value("llm_provider", "local")
        
        # Verify it was updated in memory
        assert config_manager.get_value("llm_provider") == "local"
        
        # Verify it was saved to file
        config_file = config_dir / "config.yaml"
        loaded_data = yaml.safe_load(config_file.read_text())
        assert loaded_data["llm_provider"] == "local"

    def test_config_validates_llm_provider(self, temp_dir: Path) -> None:
        """Test that invalid LLM provider raises validation error."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        with pytest.raises(ValueError, match="Invalid LLM provider"):
            config_manager.set_value("llm_provider", "invalid-provider")

    def test_config_validates_log_level(self, temp_dir: Path) -> None:
        """Test that invalid log level raises validation error."""
        config_dir = temp_dir / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        with pytest.raises(ValueError, match="Invalid log level"):
            config_manager.set_value("log_level", "INVALID")

    def test_config_handles_missing_config_file_gracefully(self, temp_dir: Path) -> None:
        """Test that missing config file creates defaults without error."""
        config_dir = temp_dir / ".agentic"
        # Don't create the directory - test auto-creation
        
        config_manager = ConfigManager(config_dir)
        config = config_manager.load()
        
        # Should create defaults without raising an exception
        assert config.llm_provider is not None
        assert config.sandbox_enabled is not None
        assert config.log_level is not None