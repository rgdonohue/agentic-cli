"""Unit tests for task template system - PoC 2."""

from pathlib import Path
import tempfile
from typing import Dict, Any

import pytest
import yaml

from agentic.tasks import TaskTemplate, TaskRegistry, ValidationError


class TestTaskTemplate:
    """Test task template parsing and validation."""

    def test_task_template_loads_from_yaml(self, temp_dir: Path) -> None:
        """Test that TaskTemplate can load from YAML file."""
        task_file = temp_dir / "test_task.yaml"
        task_data = {
            "name": "test_task",
            "version": "1.0.0", 
            "description": "A test task",
            "inputs": [
                {
                    "name": "input1",
                    "type": "string",
                    "required": True,
                    "description": "Test input"
                }
            ],
            "output": {
                "type": "file",
                "pattern": "output.txt"
            },
            "template": "Hello {{ input1 }}"
        }
        
        task_file.write_text(yaml.dump(task_data))
        
        template = TaskTemplate.from_file(task_file)
        
        assert template.name == "test_task"
        assert template.version == "1.0.0"
        assert template.description == "A test task"
        assert len(template.inputs) == 1
        assert template.inputs[0].name == "input1"

    def test_task_template_validates_required_fields(self, temp_dir: Path) -> None:
        """Test that TaskTemplate rejects templates missing required fields."""
        task_file = temp_dir / "invalid_task.yaml"
        incomplete_data = {
            "name": "incomplete_task"
            # Missing required fields: version, description, inputs, output, template
        }
        
        task_file.write_text(yaml.dump(incomplete_data))
        
        with pytest.raises(ValidationError, match="Missing required field"):
            TaskTemplate.from_file(task_file)

    def test_task_template_validates_input_schema(self, temp_dir: Path) -> None:
        """Test that TaskTemplate validates input parameter definitions."""
        task_file = temp_dir / "bad_inputs.yaml"
        bad_data = {
            "name": "bad_task",
            "version": "1.0.0",
            "description": "Task with invalid inputs",
            "inputs": [
                {
                    "name": "invalid_input",
                    "type": "invalid_type",  # Invalid type
                    "required": True
                }
            ],
            "output": {"type": "file", "pattern": "out.txt"},
            "template": "test"
        }
        
        task_file.write_text(yaml.dump(bad_data))
        
        with pytest.raises(ValidationError, match="Invalid input type"):
            TaskTemplate.from_file(task_file)

    def test_task_template_substitutes_variables(self, temp_dir: Path) -> None:
        """Test that TaskTemplate correctly substitutes template variables."""
        task_file = temp_dir / "substitution_task.yaml"
        task_data = {
            "name": "sub_task",
            "version": "1.0.0",
            "description": "Variable substitution test",
            "inputs": [
                {"name": "name", "type": "string", "required": True},
                {"name": "greeting", "type": "string", "required": False, "default": "Hello"}
            ],
            "output": {"type": "file", "pattern": "{{ name }}.txt"},
            "template": "{{ greeting }} {{ name }}!"
        }
        
        task_file.write_text(yaml.dump(task_data))
        template = TaskTemplate.from_file(task_file)
        
        # Test variable substitution
        variables = {"name": "World", "greeting": "Hi"}
        result = template.render(variables)
        
        assert result.content == "Hi World!"
        assert result.output_file == "World.txt"

    def test_task_template_uses_default_values(self, temp_dir: Path) -> None:
        """Test that TaskTemplate uses default values for optional inputs."""
        task_file = temp_dir / "defaults_task.yaml"
        task_data = {
            "name": "defaults_task",
            "version": "1.0.0",
            "description": "Test default values",
            "inputs": [
                {"name": "required_input", "type": "string", "required": True},
                {"name": "optional_input", "type": "string", "required": False, "default": "default_value"}
            ],
            "output": {"type": "file", "pattern": "output.txt"},
            "template": "{{ required_input }} - {{ optional_input }}"
        }
        
        task_file.write_text(yaml.dump(task_data))
        template = TaskTemplate.from_file(task_file)
        
        # Only provide required input
        variables = {"required_input": "test"}
        result = template.render(variables)
        
        assert result.content == "test - default_value"

    def test_task_template_validates_required_inputs(self, temp_dir: Path) -> None:
        """Test that TaskTemplate validates required inputs are provided."""
        task_file = temp_dir / "required_task.yaml"
        task_data = {
            "name": "required_task",
            "version": "1.0.0",
            "description": "Test required validation",
            "inputs": [
                {"name": "required_input", "type": "string", "required": True}
            ],
            "output": {"type": "file", "pattern": "output.txt"},
            "template": "{{ required_input }}"
        }
        
        task_file.write_text(yaml.dump(task_data))
        template = TaskTemplate.from_file(task_file)
        
        # Missing required input
        with pytest.raises(ValidationError, match="Required input 'required_input' not provided"):
            template.render({})


class TestTaskRegistry:
    """Test task registry functionality."""

    def test_task_registry_loads_builtin_tasks(self) -> None:
        """Test that TaskRegistry finds and loads built-in tasks."""
        registry = TaskRegistry()
        
        builtin_tasks = registry.list_builtin_tasks()
        
        # Should find at least our sample python_function task
        assert len(builtin_tasks) > 0
        assert any(task.name == "python_function" for task in builtin_tasks)

    def test_task_registry_loads_from_directory(self, temp_dir: Path) -> None:
        """Test that TaskRegistry can load tasks from a custom directory."""
        # Create a custom task
        task_dir = temp_dir / "custom_tasks"
        task_dir.mkdir()
        
        custom_task = task_dir / "custom.yaml"
        task_data = {
            "name": "custom_task",
            "version": "1.0.0",
            "description": "Custom task",
            "inputs": [],
            "output": {"type": "file", "pattern": "custom.txt"},
            "template": "Custom content"
        }
        custom_task.write_text(yaml.dump(task_data))
        
        registry = TaskRegistry(task_dirs=[task_dir])
        tasks = registry.list_tasks()
        
        assert any(task.name == "custom_task" for task in tasks)

    def test_task_registry_gets_task_by_name(self) -> None:
        """Test that TaskRegistry can retrieve specific tasks by name."""
        registry = TaskRegistry()
        
        task = registry.get_task("python_function")
        
        assert task is not None
        assert task.name == "python_function"

    def test_task_registry_handles_missing_tasks(self) -> None:
        """Test that TaskRegistry handles requests for non-existent tasks."""
        registry = TaskRegistry()
        
        task = registry.get_task("nonexistent_task")
        
        assert task is None

    def test_task_registry_validates_task_files(self, temp_dir: Path) -> None:
        """Test that TaskRegistry skips invalid task files."""
        task_dir = temp_dir / "invalid_tasks"
        task_dir.mkdir()
        
        # Create invalid task file
        invalid_task = task_dir / "invalid.yaml"
        invalid_task.write_text("invalid: yaml: content:")
        
        # Registry should not crash, just skip invalid files
        registry = TaskRegistry(task_dirs=[task_dir])
        tasks = registry.list_tasks()
        
        # Should be empty since the file is invalid
        assert len([t for t in tasks if "invalid" in t.name]) == 0