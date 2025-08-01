"""Task template system for structured AI task definitions."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re

import yaml
from pydantic import BaseModel, field_validator
from jinja2 import Template, Environment


class ValidationError(Exception):
    """Raised when task template validation fails."""
    pass


class TaskInput(BaseModel):
    """Definition of a task input parameter."""
    
    name: str
    type: str
    required: bool = True
    description: str = ""
    pattern: Optional[str] = None
    default: Optional[Any] = None
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that input type is supported."""
        valid_types = ["string", "integer", "float", "boolean", "array", "object"]
        if v not in valid_types:
            raise ValueError(f"Invalid input type: {v}. Must be one of {valid_types}")
        return v


class TaskOutput(BaseModel):
    """Definition of task output specification."""
    
    type: str
    pattern: str
    location: str = ""
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that output type is supported."""
        valid_types = ["file", "directory", "string"]
        if v not in valid_types:
            raise ValueError(f"Invalid output type: {v}. Must be one of {valid_types}")
        return v


class TaskResult(BaseModel):
    """Result of rendering a task template."""
    
    content: str
    output_file: str
    validation_commands: List[str] = []


class TaskTemplate(BaseModel):
    """A structured task definition for AI code generation."""
    
    name: str
    version: str
    description: str
    inputs: List[TaskInput]
    output: TaskOutput
    validation: List[str] = []
    template: str
    
    @classmethod
    def from_file(cls, file_path: Path) -> "TaskTemplate":
        """Load task template from YAML file."""
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise ValidationError(f"Failed to load task file {file_path}: {e}")
        
        # Validate required fields
        required_fields = ["name", "version", "description", "inputs", "output", "template"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        try:
            # Convert input dicts to TaskInput objects
            if "inputs" in data:
                data["inputs"] = [TaskInput(**input_data) for input_data in data["inputs"]]
            
            # Convert output dict to TaskOutput object
            if "output" in data:
                data["output"] = TaskOutput(**data["output"])
            
            return cls(**data)
        
        except Exception as e:
            raise ValidationError(f"Invalid task template format: {e}")
    
    def render(self, variables: Dict[str, Any]) -> TaskResult:
        """Render the task template with provided variables."""
        # Validate required inputs are provided
        for input_def in self.inputs:
            if input_def.required and input_def.name not in variables:
                raise ValidationError(f"Required input '{input_def.name}' not provided")
        
        # Apply default values for missing optional inputs
        final_variables = {}
        for input_def in self.inputs:
            if input_def.name in variables:
                final_variables[input_def.name] = variables[input_def.name]
            elif input_def.default is not None:
                final_variables[input_def.name] = input_def.default
        
        # Validate input patterns
        for input_def in self.inputs:
            if input_def.pattern and input_def.name in final_variables:
                value = str(final_variables[input_def.name])
                if not re.match(input_def.pattern, value):
                    raise ValidationError(
                        f"Input '{input_def.name}' value '{value}' does not match pattern '{input_def.pattern}'"
                    )
        
        # Render template content
        try:
            jinja_template = Template(self.template)
            content = jinja_template.render(**final_variables)
        except Exception as e:
            raise ValidationError(f"Template rendering failed: {e}")
        
        # Render output file pattern
        try:
            output_template = Template(self.output.pattern)
            output_file = output_template.render(**final_variables)
        except Exception as e:
            raise ValidationError(f"Output pattern rendering failed: {e}")
        
        # Render validation commands
        validation_commands = []
        for cmd_template in self.validation:
            try:
                cmd = Template(cmd_template).render(
                    output_file=output_file,
                    **final_variables
                )
                validation_commands.append(cmd)
            except Exception as e:
                raise ValidationError(f"Validation command rendering failed: {e}")
        
        return TaskResult(
            content=content,
            output_file=output_file,
            validation_commands=validation_commands
        )


class TaskRegistry:
    """Registry for managing and loading task templates."""
    
    def __init__(self, task_dirs: Optional[List[Path]] = None):
        """Initialize task registry with search directories."""
        self.task_dirs = task_dirs or []
        self._builtin_dir = Path(__file__).parent.parent.parent / "tasks" / "builtin"
        self._tasks_cache: Dict[str, TaskTemplate] = {}
    
    def list_builtin_tasks(self) -> List[TaskTemplate]:
        """List all built-in task templates."""
        return self._load_tasks_from_dir(self._builtin_dir)
    
    def list_tasks(self) -> List[TaskTemplate]:
        """List all available task templates."""
        all_tasks = []
        
        # Load built-in tasks
        all_tasks.extend(self.list_builtin_tasks())
        
        # Load tasks from custom directories
        for task_dir in self.task_dirs:
            all_tasks.extend(self._load_tasks_from_dir(task_dir))
        
        return all_tasks
    
    def get_task(self, name: str) -> Optional[TaskTemplate]:
        """Get a specific task template by name."""
        if name in self._tasks_cache:
            return self._tasks_cache[name]
        
        # Search all available tasks
        for task in self.list_tasks():
            if task.name == name:
                self._tasks_cache[name] = task
                return task
        
        return None
    
    def _load_tasks_from_dir(self, task_dir: Path) -> List[TaskTemplate]:
        """Load all task templates from a directory."""
        tasks = []
        
        if not task_dir.exists() or not task_dir.is_dir():
            return tasks
        
        for yaml_file in task_dir.glob("*.yaml"):
            try:
                task = TaskTemplate.from_file(yaml_file)
                tasks.append(task)
            except ValidationError:
                # Skip invalid task files
                continue
            except Exception:
                # Skip files that can't be processed
                continue
        
        return tasks