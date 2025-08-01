"""LLM provider abstraction for code generation."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import asyncio
import random


class LLMError(Exception):
    """Raised when LLM operations fail."""
    pass


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    
    content: str
    provider: str
    tokens_used: int
    model: str = "unknown"


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Generate code from a prompt with optional context."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider for code generation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        if not api_key:
            raise LLMError("API key is required for OpenAI provider")
        
        self.api_key = api_key
        self.model = model
        self._client = None
    
    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Generate code using OpenAI API."""
        try:
            # Lazy import to avoid dependency issues in tests
            if self._client is None:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            
            # Build system prompt based on context
            system_prompt = self._build_system_prompt(context or {})
            
            # Prepare API parameters
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": context.get("max_tokens", 1000) if context else 1000,
                "temperature": context.get("temperature", 0.2) if context else 0.2
            }
            
            response = await self._client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content
            tokens_used = getattr(response.usage, 'total_tokens', 0)
            
            return LLMResponse(
                content=content,
                provider="openai",
                tokens_used=tokens_used,
                model=self.model
            )
            
        except Exception as e:
            raise LLMError(f"OpenAI API error: {str(e)}") from e
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt from context."""
        language = context.get("language", "python")
        style = context.get("style", "clean and readable")
        
        return f"""You are an expert software engineer. Generate {language} code that is:
- {style}
- Well-documented with clear comments
- Following best practices and conventions
- Production-ready and maintainable
- Secure and safe

Focus on code generation only. Do not include explanations unless requested."""


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, simulate_error: bool = False):
        self.simulate_error = simulate_error
        self._response_templates = {
            "python": [
                "def {function_name}():\n    '''Generated function'''\n    return 'Generated result'",
                "class {class_name}:\n    '''Generated class'''\n    \n    def __init__(self):\n        self.value = 'generated'"
            ],
            "javascript": [
                "function {function_name}() {\n    // Generated function\n    return 'Generated result';\n}",
                "const {function_name} = () => {\n    // Generated arrow function\n    return 'Generated result';\n};"
            ],
            "default": [
                "// Generated code\nfunction generatedFunction() {\n    return 'Generated content';\n}"
            ]
        }
    
    async def generate_code(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Generate mock code for testing."""
        if self.simulate_error:
            raise LLMError("Simulated LLM error for testing")
        
        # Simulate async operation
        await asyncio.sleep(0.01)
        
        context = context or {}
        language = context.get("language", "python")
        
        # Generate contextually appropriate response
        templates = self._response_templates.get(language, self._response_templates["default"])
        template = random.choice(templates)
        
        # Simple template substitution for common patterns
        content = template
        if "{function_name}" in content:
            function_name = self._extract_function_name(prompt) or "generated_function"
            content = content.replace("{function_name}", function_name)
        
        if "{class_name}" in content:
            class_name = self._extract_class_name(prompt) or "GeneratedClass"
            content = content.replace("{class_name}", class_name)
        
        # Add some variety to the response
        if "Create a function" in prompt or "function" in prompt.lower():
            if language == "python":
                content = f"def generated_function():\n    '''Generated from prompt: {prompt[:50]}...'''\n    return 'Hello, World!'"
            else:
                content = f"function generatedFunction() {{\n    // Generated from prompt: {prompt[:50]}...\n    return 'Hello, World!';\n}}"
        
        return LLMResponse(
            content=content,
            provider="mock",
            tokens_used=random.randint(50, 200),
            model="mock-gpt-4"
        )
    
    def _extract_function_name(self, prompt: str) -> Optional[str]:
        """Extract function name from prompt if present."""
        # Simple regex to find function names in prompts
        patterns = [
            r"function\s+named\s+(\w+)",
            r"function\s+called\s+(\w+)",
            r"(\w+)\s+function",
            r"def\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_class_name(self, prompt: str) -> Optional[str]:
        """Extract class name from prompt if present."""
        patterns = [
            r"class\s+named\s+(\w+)",
            r"class\s+called\s+(\w+)",
            r"(\w+)\s+class",
            r"class\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


def create_llm_provider(provider_type: str = "mock", **kwargs) -> LLMProvider:
    """Factory function to create LLM providers."""
    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type == "mock":
        return MockLLMProvider(**kwargs)
    else:
        raise LLMError(f"Unknown provider type: {provider_type}")