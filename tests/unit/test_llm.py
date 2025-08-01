"""Unit tests for LLM provider abstraction - PoC 4."""

from unittest.mock import AsyncMock, Mock
import pytest

from agentic.llm import LLMProvider, OpenAIProvider, LLMError, LLMResponse


class TestLLMProvider:
    """Test LLM provider interface and implementations."""

    def test_llm_provider_is_abstract(self) -> None:
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()

    @pytest.mark.asyncio
    async def test_openai_provider_generates_code(self) -> None:
        """Test that OpenAI provider can generate code from prompts."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "def hello():\n    return 'Hello, World!'"
        mock_response.usage.total_tokens = 150
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OpenAIProvider(api_key="test-key")
        provider._client = mock_client
        
        response = await provider.generate_code(
            prompt="Create a Python function that returns 'Hello, World!'",
            context={"language": "python"}
        )
        
        assert isinstance(response, LLMResponse)
        assert "def hello():" in response.content
        assert response.provider == "openai"
        assert isinstance(response.tokens_used, int)

    @pytest.mark.asyncio
    async def test_openai_provider_handles_api_errors(self) -> None:
        """Test that OpenAI provider handles API errors gracefully."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        provider = OpenAIProvider(api_key="test-key")
        provider._client = mock_client
        
        with pytest.raises(LLMError, match="OpenAI API error"):
            await provider.generate_code("test prompt")

    @pytest.mark.asyncio
    async def test_openai_provider_validates_api_key(self) -> None:
        """Test that OpenAI provider validates API key."""
        with pytest.raises(LLMError, match="API key is required"):
            OpenAIProvider(api_key="")
        
        with pytest.raises(LLMError, match="API key is required"):
            OpenAIProvider(api_key=None)

    def test_llm_response_creation(self) -> None:
        """Test LLMResponse dataclass creation and properties."""
        response = LLMResponse(
            content="Generated code",
            provider="test-provider",
            tokens_used=150,
            model="gpt-4"
        )
        
        assert response.content == "Generated code"
        assert response.provider == "test-provider"
        assert response.tokens_used == 150
        assert response.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_openai_provider_respects_context_parameters(self) -> None:
        """Test that OpenAI provider uses context parameters correctly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "# Generated code with context"
        mock_response.usage.total_tokens = 200
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        provider = OpenAIProvider(api_key="test-key")
        provider._client = mock_client
        
        context = {
            "language": "python",
            "style": "functional",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        await provider.generate_code("Create a function", context=context)
        
        # Verify the call was made with correct parameters
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["max_tokens"] == 500
        assert call_args[1]["temperature"] == 0.7
        assert "python" in str(call_args[1]["messages"])


class TestMockLLMProvider:
    """Test mock LLM provider for testing."""

    @pytest.mark.asyncio
    async def test_mock_provider_returns_deterministic_responses(self) -> None:
        """Test that mock provider returns predictable responses for testing."""
        from agentic.llm import MockLLMProvider
        
        provider = MockLLMProvider()
        
        response = await provider.generate_code("Create a Python function")
        
        assert isinstance(response, LLMResponse)
        assert response.provider == "mock"
        assert response.tokens_used > 0
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_mock_provider_can_simulate_errors(self) -> None:
        """Test that mock provider can simulate API errors for testing."""
        from agentic.llm import MockLLMProvider
        
        provider = MockLLMProvider(simulate_error=True)
        
        with pytest.raises(LLMError, match="Simulated LLM error"):
            await provider.generate_code("test prompt")

    @pytest.mark.asyncio
    async def test_mock_provider_respects_language_context(self) -> None:
        """Test that mock provider generates language-appropriate responses."""
        from agentic.llm import MockLLMProvider
        
        provider = MockLLMProvider()
        
        python_response = await provider.generate_code(
            "Create a function", 
            context={"language": "python"}
        )
        
        javascript_response = await provider.generate_code(
            "Create a function", 
            context={"language": "javascript"}
        )
        
        assert "def " in python_response.content or "function" in python_response.content
        assert "function" in javascript_response.content or "const" in javascript_response.content