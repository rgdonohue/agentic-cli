"""Configuration management for Agentic CLI."""

from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, field_validator


class Config(BaseModel):
    """Agentic CLI configuration model."""
    
    llm_provider: str = "openai"
    sandbox_enabled: bool = True
    log_level: str = "INFO"
    api_key: str = ""
    max_tokens: int = 4000
    temperature: float = 0.1
    
    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported."""
        valid_providers = ["openai", "anthropic", "claude", "local", "mock"]
        if v not in valid_providers:
            raise ValueError(f"Invalid LLM provider: {v}. Must be one of {valid_providers}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class ConfigManager:
    """Manages loading, saving, and updating configuration."""
    
    def __init__(self, config_dir: Path) -> None:
        """Initialize config manager with config directory path."""
        self.config_dir = config_dir
        self.config_file = config_dir / "config.yaml"
        self._config: Config | None = None
    
    def load(self) -> Config:
        """Load configuration from file or create default."""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            # Load existing config
            try:
                with open(self.config_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    self._config = Config(**config_data)
            except Exception as e:
                # If config is corrupted, create default and save
                self._config = Config()
                self.save(self._config)
        else:
            # Create default config
            self._config = Config()
            self.save(self._config)
        
        return self._config
    
    def save(self, config: Config) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, "w") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
        
        self._config = config
    
    def get_value(self, key: str) -> Any:
        """Get a configuration value by key."""
        if self._config is None:
            self.load()
        
        if not hasattr(self._config, key):
            raise KeyError(f"Configuration key '{key}' not found")
        
        return getattr(self._config, key)
    
    def set_value(self, key: str, value: Any) -> None:
        """Set a configuration value and save to file."""
        if self._config is None:
            self.load()
        
        if not hasattr(self._config, key):
            raise KeyError(f"Configuration key '{key}' not found")
        
        # Create new config with updated value
        config_dict = self._config.model_dump()
        config_dict[key] = value
        
        # Validate by creating new Config instance
        new_config = Config(**config_dict)
        
        # Save the validated config
        self.save(new_config)