"""Unit tests for Generator Agent - PoC 4."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from agentic.generator import GeneratorAgent, GenerationError, GenerationResult
from agentic.llm import LLMResponse, MockLLMProvider
from agentic.tasks import TaskTemplate, TaskInput, TaskOutput


class TestGeneratorAgent:
    """Test core Generator Agent functionality."""

    @pytest.mark.asyncio
    async def test_generator_creates_files_from_task_template(self, temp_dir: Path) -> None:
        """Test that Generator can create files using task templates."""
        # Create a simple task template
        task_template = TaskTemplate(
            name="simple_function",
            version="1.0.0",
            description="Generate a simple Python function",
            inputs=[
                TaskInput(name="function_name", type="string", required=True),
                TaskInput(name="return_value", type="string", required=True)
            ],
            output=TaskOutput(
                type="file",
                pattern="{{ function_name }}.py",
                location="src/"
            ),
            validation=[],
            template="def {{ function_name }}():\n    return '{{ return_value }}'"
        )
        
        # Mock LLM provider
        mock_llm = MockLLMProvider()
        
        # Create generator
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        # Generate code
        inputs = {"function_name": "hello", "return_value": "Hello, World!"}
        result = await generator.generate_from_template(task_template, inputs)
        
        assert isinstance(result, GenerationResult)
        assert len(result.files) == 1
        assert "src/hello.py" in result.files
        assert "def hello():" in result.files["src/hello.py"]
        assert "Hello, World!" in result.files["src/hello.py"]

    @pytest.mark.asyncio
    async def test_generator_handles_complex_task_templates(self, temp_dir: Path) -> None:
        """Test Generator with complex templates requiring LLM enhancement."""
        # Create FastAPI route template (from our builtin tasks)
        task_template = TaskTemplate(
            name="fastapi_route",
            version="1.0.0",
            description="Generate FastAPI route with LLM enhancement",
            inputs=[
                TaskInput(name="route_path", type="string", required=True),
                TaskInput(name="method", type="string", required=True),
                TaskInput(name="function_name", type="string", required=True),
                TaskInput(name="description", type="string", required=True)
            ],
            output=TaskOutput(
                type="file",
                pattern="routes/{{ function_name }}.py",
                location="src/"
            ),
            validation=[],
            template="""from fastapi import APIRouter

router = APIRouter()

@router.{{ method.lower() }}("{{ route_path }}")
async def {{ function_name }}():
    '''{{ description }}'''
    # TODO: Implement {{ function_name }} logic
    return {"message": "{{ description }}"}"""
        )
        
        # Mock LLM to enhance the template
        mock_llm = AsyncMock()
        mock_llm.generate_code.return_value = LLMResponse(
            content="""from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int) -> Dict[str, Any]:
    '''Get user by ID with proper validation'''
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Simulate database lookup
    user_data = {"id": user_id, "name": f"User {user_id}", "active": True}
    return user_data""",
            provider="mock",
            tokens_used=150,
            model="gpt-4"
        )
        
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        inputs = {
            "route_path": "/users/{user_id}",
            "method": "GET",
            "function_name": "get_user",
            "description": "Get user by ID with proper validation"
        }
        
        result = await generator.generate_from_template(task_template, inputs, enhance_with_llm=True)
        
        assert len(result.files) == 1
        assert "src/routes/get_user.py" in result.files
        content = result.files["src/routes/get_user.py"]
        assert "HTTPException" in content
        assert "user_id: int" in content
        assert "Invalid user ID" in content

    @pytest.mark.asyncio
    async def test_generator_validates_template_inputs(self, temp_dir: Path) -> None:
        """Test that Generator validates required inputs."""
        task_template = TaskTemplate(
            name="test_task",
            version="1.0.0",
            description="Test task",
            inputs=[
                TaskInput(name="required_field", type="string", required=True),
                TaskInput(name="optional_field", type="string", required=False, default="default")
            ],
            output=TaskOutput(type="file", pattern="test.py", location=""),
            validation=[],
            template="# {{ required_field }} - {{ optional_field }}"
        )
        
        mock_llm = MockLLMProvider()
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        # Missing required field should raise error
        with pytest.raises(GenerationError, match="Missing required input"):
            await generator.generate_from_template(task_template, {})
        
        # Valid inputs should work
        inputs = {"required_field": "test_value"}
        result = await generator.generate_from_template(task_template, inputs)
        
        assert len(result.files) == 1
        assert "test_value" in result.files["test.py"]
        assert "default" in result.files["test.py"]

    @pytest.mark.asyncio
    async def test_generator_handles_llm_errors(self, temp_dir: Path) -> None:
        """Test that Generator handles LLM provider errors gracefully."""
        task_template = TaskTemplate(
            name="test_task",
            version="1.0.0",
            description="Test task",
            inputs=[],
            output=TaskOutput(type="file", pattern="test.py", location=""),
            validation=[],
            template="# Simple template"
        )
        
        # Mock LLM that raises errors
        mock_llm = MockLLMProvider(simulate_error=True)
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        with pytest.raises(GenerationError, match="LLM generation failed"):
            await generator.generate_from_template(task_template, {}, enhance_with_llm=True)

    @pytest.mark.asyncio
    async def test_generator_sanitizes_output(self, temp_dir: Path) -> None:
        """Test that Generator sanitizes potentially dangerous output."""
        task_template = TaskTemplate(
            name="test_task",
            version="1.0.0", 
            description="Test task",
            inputs=[],
            output=TaskOutput(type="file", pattern="test.py", location=""),
            validation=[],
            template="# Safe template"
        )
        
        # Mock LLM that returns potentially dangerous content
        mock_llm = AsyncMock()
        mock_llm.generate_code.return_value = LLMResponse(
            content="""import os
import subprocess

# Dangerous code that tries to access system
os.system("rm -rf /")
subprocess.run(["curl", "http://malicious-site.com"])

def legitimate_function():
    return "Hello, World!"
""",
            provider="mock",
            tokens_used=100,
            model="gpt-4"
        )
        
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        result = await generator.generate_from_template(task_template, {}, enhance_with_llm=True)
        
        # Verify dangerous content is removed or commented out
        content = result.files["test.py"]
        assert "# SECURITY WARNING:" in content or "os.system" not in content
        assert "legitimate_function" in content  # Safe content should remain

    def test_generation_result_properties(self) -> None:
        """Test GenerationResult dataclass properties."""
        files = {"main.py": "print('hello')", "utils.py": "def helper(): pass"}
        metadata = {"template": "python_function", "enhanced": True}
        
        result = GenerationResult(
            files=files,
            metadata=metadata,
            template_name="python_function"
        )
        
        assert result.files == files
        assert result.metadata == metadata
        assert result.template_name == "python_function"
        assert len(result.files) == 2

    @pytest.mark.asyncio
    async def test_generator_creates_files_in_specified_location(self, temp_dir: Path) -> None:
        """Test Generator respects output location configuration."""
        task_template = TaskTemplate(
            name="located_task",
            version="1.0.0",
            description="Generate file in specific location",
            inputs=[
                TaskInput(name="module_name", type="string", required=True)
            ],
            output=TaskOutput(
                type="file",
                pattern="{{ module_name }}.py",
                location="src/modules/"
            ),
            validation=[],
            template="# {{ module_name }} module\ndef main():\n    pass"
        )
        
        mock_llm = MockLLMProvider()
        generator = GeneratorAgent(llm_provider=mock_llm, project_dir=temp_dir)
        
        inputs = {"module_name": "mymodule"}
        result = await generator.generate_from_template(task_template, inputs)
        
        assert len(result.files) == 1
        assert "src/modules/mymodule.py" in result.files
        assert "# mymodule module" in result.files["src/modules/mymodule.py"]
        assert "def main():" in result.files["src/modules/mymodule.py"]