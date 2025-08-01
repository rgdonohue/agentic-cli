"""Generator Agent for AI-powered code generation."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from jinja2 import Template, TemplateError

from .llm import LLMProvider, LLMError
from .tasks import TaskTemplate, TaskInput


class GenerationError(Exception):
    """Raised when code generation fails."""
    pass


@dataclass
class GenerationResult:
    """Result of code generation from a task template."""
    
    files: Dict[str, str]  # filepath -> content
    metadata: Dict[str, Any]
    template_name: str


class GeneratorAgent:
    """AI-powered code generator using task templates."""
    
    def __init__(self, llm_provider: LLMProvider, project_dir: Path):
        self.llm_provider = llm_provider
        self.project_dir = project_dir
        self._security_patterns = self._compile_security_patterns()
    
    async def generate_from_template(
        self,
        task_template: TaskTemplate,
        inputs: Dict[str, Any],
        enhance_with_llm: bool = False
    ) -> GenerationResult:
        """Generate code from a task template with optional LLM enhancement."""
        try:
            # Validate inputs against template requirements
            self._validate_inputs(task_template, inputs)
            
            # Add defaults for optional inputs
            complete_inputs = self._add_default_values(task_template, inputs)
            
            # Generate base content from template
            files = self._render_template(task_template, complete_inputs)
            
            # Optionally enhance with LLM
            if enhance_with_llm:
                files = await self._enhance_with_llm(task_template, files, complete_inputs)
            
            # Sanitize output for security
            files = self._sanitize_output(files)
            
            return GenerationResult(
                files=files,
                metadata={
                    "template": task_template.name,
                    "version": task_template.version,
                    "enhanced": enhance_with_llm,
                    "inputs": complete_inputs
                },
                template_name=task_template.name
            )
            
        except Exception as e:
            raise GenerationError(f"Generation failed: {str(e)}") from e
    
    def _validate_inputs(self, task_template: TaskTemplate, inputs: Dict[str, Any]) -> None:
        """Validate that all required inputs are present."""
        required_inputs = [inp.name for inp in task_template.inputs if inp.required]
        missing_inputs = [name for name in required_inputs if name not in inputs]
        
        if missing_inputs:
            raise GenerationError(
                f"Missing required input(s): {', '.join(missing_inputs)}"
            )
        
        # Validate input patterns if specified
        for task_input in task_template.inputs:
            if task_input.name in inputs and hasattr(task_input, 'pattern') and task_input.pattern:
                value = str(inputs[task_input.name])
                if not re.match(task_input.pattern, value):
                    raise GenerationError(
                        f"Input '{task_input.name}' does not match required pattern: {task_input.pattern}"
                    )
    
    def _add_default_values(self, task_template: TaskTemplate, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for optional inputs."""
        complete_inputs = inputs.copy()
        
        for task_input in task_template.inputs:
            if task_input.name not in complete_inputs and hasattr(task_input, 'default') and task_input.default is not None:
                complete_inputs[task_input.name] = task_input.default
        
        return complete_inputs
    
    def _render_template(self, task_template: TaskTemplate, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Render Jinja2 templates to generate base content."""
        files = {}
        
        try:
            if isinstance(task_template.template, str):
                # Single file template
                file_path = self._render_file_path(task_template, inputs)
                content = Template(task_template.template).render(**inputs)
                files[file_path] = content
                
            elif isinstance(task_template.template, dict):
                # Multiple file templates
                for file_pattern, template_content in task_template.template.items():
                    file_path = Template(file_pattern).render(**inputs)
                    
                    # Add location prefix if specified
                    if hasattr(task_template, 'output') and task_template.output.get('location'):
                        location = Template(task_template.output['location']).render(**inputs)
                        file_path = f"{location.rstrip('/')}/{file_path}"
                    
                    content = Template(template_content).render(**inputs)
                    files[file_path] = content
            
            else:
                raise GenerationError("Invalid template format")
                
        except TemplateError as e:
            raise GenerationError(f"Template rendering failed: {str(e)}") from e
        
        return files
    
    def _render_file_path(self, task_template: TaskTemplate, inputs: Dict[str, Any]) -> str:
        """Render the output file path for single-file templates."""
        if not task_template.output:
            raise GenerationError("Task template missing output specification")
        
        output = task_template.output
        pattern = output.pattern
        location = output.location or ''
        
        # Render pattern with inputs
        file_name = Template(pattern).render(**inputs)
        
        # Combine with location if specified
        if location:
            location = Template(location).render(**inputs)
            return f"{location.rstrip('/')}/{file_name}"
        
        return file_name
    
    async def _enhance_with_llm(
        self,
        task_template: TaskTemplate,
        files: Dict[str, str],
        inputs: Dict[str, Any]
    ) -> Dict[str, str]:
        """Enhance generated content using LLM."""
        enhanced_files = {}
        
        for file_path, content in files.items():
            try:
                # Build enhancement prompt
                prompt = self._build_enhancement_prompt(task_template, file_path, content, inputs)
                
                # Determine language from file extension
                context = {
                    "language": self._detect_language(file_path),
                    "style": "professional",
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
                
                # Generate enhanced content
                response = await self.llm_provider.generate_code(prompt, context)
                enhanced_files[file_path] = response.content
                
            except LLMError as e:
                raise GenerationError(f"LLM generation failed: {str(e)}") from e
        
        return enhanced_files
    
    def _build_enhancement_prompt(
        self,
        task_template: TaskTemplate,
        file_path: str,
        content: str,
        inputs: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM enhancement."""
        return f"""Enhance and improve the following generated code:

Task: {task_template.description}
File: {file_path}
Context: {inputs}

Current generated code:
```
{content}
```

Please enhance this code by:
1. Adding proper error handling and validation
2. Improving code structure and readability
3. Adding comprehensive documentation
4. Following best practices and conventions
5. Making it production-ready

Return only the enhanced code, no explanations."""
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.html': 'html',
            '.css': 'css'
        }
        
        return language_map.get(extension, 'text')
    
    def _sanitize_output(self, files: Dict[str, str]) -> Dict[str, str]:
        """Sanitize generated content for security issues."""
        sanitized_files = {}
        
        for file_path, content in files.items():
            sanitized_content = self._sanitize_content(content)
            sanitized_files[file_path] = sanitized_content
        
        return sanitized_files
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize individual file content for security issues."""
        lines = content.split('\n')
        sanitized_lines = []
        warnings = []
        
        for line in lines:
            # Check for dangerous patterns
            is_dangerous = False
            for pattern, warning in self._security_patterns:
                if pattern.search(line):
                    is_dangerous = True
                    warnings.append(f"SECURITY WARNING: {warning}")
                    # Comment out dangerous line
                    sanitized_lines.append(f"# SECURITY WARNING: {warning}")
                    sanitized_lines.append(f"# {line}")
                    break
            
            if not is_dangerous:
                sanitized_lines.append(line)
        
        # Add warnings at the top if any were found
        if warnings:
            warning_header = [
                "# SECURITY WARNINGS DETECTED:",
                "# The following potentially dangerous code has been commented out:",
                "# Please review and implement proper security measures.",
                ""
            ]
            sanitized_lines = warning_header + sanitized_lines
        
        return '\n'.join(sanitized_lines)
    
    def _compile_security_patterns(self) -> List[tuple]:
        """Compile regex patterns for detecting security issues."""
        patterns = [
            (re.compile(r'os\.system\s*\('), "Dangerous system command execution"),
            (re.compile(r'subprocess\.(run|call|Popen).*shell\s*=\s*True'), "Shell injection risk"),
            (re.compile(r'eval\s*\('), "Code injection via eval()"),
            (re.compile(r'exec\s*\('), "Code injection via exec()"),
            (re.compile(r'__import__\s*\('), "Dynamic import security risk"),
            (re.compile(r'open\s*\([^)]*["\']\/'), "Absolute path file access"),
            (re.compile(r'rm\s+-rf\s+\/'), "Dangerous file deletion"),
            (re.compile(r'curl.*http[s]?:\/\/'), "Unvalidated external requests"),
            (re.compile(r'wget.*http[s]?:\/\/'), "Unvalidated external requests"),
            (re.compile(r'input\s*\([^)]*\).*exec'), "User input to code execution"),
            (re.compile(r'pickle\.loads?\s*\('), "Unsafe deserialization"),
        ]
        
        return patterns


async def generate_code_from_task(
    task_template: TaskTemplate,
    inputs: Dict[str, Any],
    llm_provider: LLMProvider,
    project_dir: Path,
    enhance_with_llm: bool = False
) -> GenerationResult:
    """Convenience function for generating code from a task template."""
    generator = GeneratorAgent(llm_provider, project_dir)
    return await generator.generate_from_template(task_template, inputs, enhance_with_llm)