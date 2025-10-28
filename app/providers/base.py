"""
Abstract base classes for LLM providers.

Defines the interface that all LLM providers must implement,
ensuring consistency and enabling easy extension to new providers.
"""

from abc import ABC, abstractmethod
from typing import TypedDict, Literal


class SummaryResult(TypedDict):
    """
    Result structure for summarization operations.
    
    Provides a consistent interface for summarization results across
    all LLM providers with comprehensive metadata.
    
    Attributes:
        summary: Generated summary text
        usage: Token usage statistics
        model: Model identifier used for generation
        latency_ms: Request processing time in milliseconds
    """
    summary: str
    usage: dict[str, int]
    model: str
    latency_ms: int


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Defines the interface that all LLM providers must implement,
    ensuring consistency across different providers and enabling
    easy extension to new models or services.
    
    All providers must implement the summarize method with the
    exact signature defined here to maintain compatibility.
    """
    
    @abstractmethod
    async def summarize(
        self,
        text: str,
        *,
        max_tokens: int,
        lang: str,
        tone: str
    ) -> SummaryResult:
        """
        Generate summary from input text.
        
        This is the main method that all LLM providers must implement.
        It should handle the complete summarization workflow including
        prompt construction, API calls, and result formatting.
        
        Args:
            text: Input text to summarize
            max_tokens: Maximum tokens in the generated summary
            lang: Target language for summarization ('auto', 'en', 'es', etc.)
            tone: Summary tone/style ('neutral', 'concise', 'bullet')
            
        Returns:
            SummaryResult containing the generated summary and metadata
            
        Raises:
            LLMProviderError: If summarization fails after all retries
            ValidationError: If input parameters are invalid
            
        Example:
            ```python
            provider = GeminiProvider(api_key="...")
            result = await provider.summarize(
                text="Long article text...",
                max_tokens=100,
                lang="en",
                tone="concise"
            )
            print(result["summary"])
            ```
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns:
            Provider name identifier
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name used by this provider.
        
        Returns:
            Model name identifier
        """
        pass


# Export for easy importing
__all__ = ["BaseLLMProvider", "SummaryResult"]
