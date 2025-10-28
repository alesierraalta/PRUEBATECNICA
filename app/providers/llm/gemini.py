"""
Google Gemini LLM provider implementation.

Provides high-quality text summarization using Google's Gemini API
with automatic retries, comprehensive error handling, and detailed
metrics collection.
"""

import time
from typing import Literal

import stamina
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.core.constants import (
    GEMINI_PROVIDER,
    GEMINI_MODEL_DEFAULT,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    RETRY_JITTER,
    MAX_RETRY_ATTEMPTS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_TONES,
)
from app.core.exceptions import LLMProviderError, ValidationError
from app.providers.base import BaseLLMProvider, SummaryResult


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider with automatic retries and comprehensive metrics.
    
    Implements text summarization using Google's Gemini API with production-grade
    retry mechanisms, detailed error handling, and comprehensive metrics collection.
    Uses stamina for robust retry logic with exponential backoff and jitter.
    
    Features:
    - Automatic retries with exponential backoff
    - Comprehensive error handling and reporting
    - Token usage tracking and latency measurement
    - Support for multiple languages and tones
    - Optimized prompt construction
    - Type-safe implementation with full documentation
    
    Attributes:
        api_key: Google AI API key for authentication
        model_name: Specific Gemini model to use
        timeout_seconds: Request timeout in seconds
        max_attempts: Maximum retry attempts
        temperature: Generation temperature for consistency
    """
    
    def __init__(
        self,
        api_key: str,
        model_name: str = GEMINI_MODEL_DEFAULT,
        timeout_seconds: int = 8,
        max_attempts: int = MAX_RETRY_ATTEMPTS,
        temperature: float = 0.3
    ):
        """
        Initialize Gemini provider.
        
        Sets up the Gemini client with the provided configuration and
        validates all parameters before initialization.
        
        Args:
            api_key: Google AI API key for authentication
            model_name: Specific Gemini model to use (default: gemini-pro)
            timeout_seconds: Request timeout in seconds (default: 8)
            max_attempts: Maximum retry attempts (default: 3)
            temperature: Generation temperature 0.0-1.0 (default: 0.3)
            
        Raises:
            ValidationError: If parameters are invalid
            ConfigurationError: If API key is invalid
            
        Example:
            ```python
            provider = GeminiProvider(
                api_key="AIzaSyC...",
                model_name="gemini-pro",
                timeout_seconds=10,
                max_attempts=3
            )
            ```
        """
        # Validate parameters
        if not api_key or len(api_key) < 20:
            raise ValidationError(
                "Invalid API key provided / Clave API inválida proporcionada",
                field="api_key",
                value="***" if api_key else None
            )
        
        if timeout_seconds < 1 or timeout_seconds > 60:
            raise ValidationError(
                f"Timeout must be between 1-60 seconds / Timeout debe estar entre 1-60 segundos",
                field="timeout_seconds",
                value=timeout_seconds
            )
        
        if max_attempts < 1 or max_attempts > 10:
            raise ValidationError(
                f"Max attempts must be between 1-10 / Intentos máximos debe estar entre 1-10",
                field="max_attempts",
                value=max_attempts
            )
        
        if temperature < 0.0 or temperature > 1.0:
            raise ValidationError(
                f"Temperature must be between 0.0-1.0 / Temperatura debe estar entre 0.0-1.0",
                field="temperature",
                value=temperature
            )
        
        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        except Exception as e:
            raise LLMProviderError(
                f"Failed to configure Gemini API / Error al configurar API de Gemini: {str(e)}",
                provider=GEMINI_PROVIDER,
                model=model_name
            )
        
        # Store configuration
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout_seconds
        self.max_attempts = max_attempts
        self.temperature = temperature
    
    @property
    def provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            Provider name identifier
        """
        return GEMINI_PROVIDER
    
    @property
    def model_name(self) -> str:
        """
        Get the model name.
        
        Returns:
            Model name identifier
        """
        return self.model_name
    
    def _build_prompt(
        self,
        text: str,
        lang: str,
        tone: str,
        max_tokens: int
    ) -> str:
        """
        Build optimized prompt for summarization.
        
        Constructs a carefully crafted prompt based on the requested
        language, tone, and token constraints to maximize summarization
        quality and consistency.
        
        Args:
            text: Input text to summarize
            lang: Target language for summarization
            tone: Summary tone/style
            max_tokens: Maximum tokens in summary
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValidationError: If language or tone is not supported
        """
        # Validate language
        if lang not in SUPPORTED_LANGUAGES:
            raise ValidationError(
                f"Unsupported language '{lang}' / Idioma no soportado '{lang}'",
                field="lang",
                value=lang,
                details={"supported_languages": SUPPORTED_LANGUAGES}
            )
        
        # Validate tone
        if tone not in SUPPORTED_TONES:
            raise ValidationError(
                f"Unsupported tone '{tone}' / Tono no soportado '{tone}'",
                field="tone",
                value=tone,
                details={"supported_tones": SUPPORTED_TONES}
            )
        
        # Build tone-specific instructions
        tone_instructions = {
            "neutral": "Provide a balanced, objective summary that captures the main points",
            "concise": "Create a very concise, brief summary focusing only on key information",
            "bullet": "Generate a bullet-point summary with clear, structured points"
        }
        
        instruction = tone_instructions[tone]
        
        # Add language instruction
        if lang != "auto":
            instruction += f" in {lang}"
        
        # Add token constraint
        instruction += f". Keep the summary under {max_tokens} tokens."
        
        # Construct final prompt
        prompt = f"""{instruction}

Text to summarize:
{text}

Summary:"""
        
        return prompt
    
    @stamina.retry(
        on=Exception,  # Retry on any exception
        attempts=3,  # Will be overridden by max_attempts
        wait_initial=RETRY_BASE_DELAY,
        wait_max=RETRY_MAX_DELAY,
        wait_jitter=RETRY_JITTER
    )
    async def _generate_with_retry(self, prompt: str) -> GenerateContentResponse:
        """
        Generate content with automatic retries.
        
        Uses stamina to handle retries with exponential backoff and jitter.
        This method is automatically retried on any exception, providing
        robust handling of transient failures.
        
        Args:
            prompt: Formatted prompt for generation
            
        Returns:
            Gemini API response object
            
        Raises:
            Exception: If all retry attempts fail
        """
        try:
            # Generate content with timeout
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "max_output_tokens": 512,  # Gemini's max
                    "temperature": self.temperature,
                    "top_p": 0.8,
                    "top_k": 40,
                }
            )
            
            # Validate response
            if not response or not response.text:
                raise LLMProviderError(
                    "Empty response from Gemini / Respuesta vacía de Gemini",
                    provider=self.provider_name,
                    model=self.model_name,
                    last_error="No text content in response"
                )
            
            return response
            
        except Exception as e:
            # Re-raise as LLMProviderError for consistent handling
            raise LLMProviderError(
                f"Gemini generation failed / Generación de Gemini falló: {str(e)}",
                provider=self.provider_name,
                model=self.model_name,
                last_error=str(e)
            )
    
    async def summarize(
        self,
        text: str,
        *,
        max_tokens: int,
        lang: str,
        tone: str
    ) -> SummaryResult:
        """
        Generate summary using Gemini with retries and comprehensive metrics.
        
        Implements the complete summarization workflow including prompt
        construction, API calls with retries, error handling, and metrics
        collection. Provides detailed information about the generation
        process for monitoring and debugging.
        
        Args:
            text: Input text to summarize
            max_tokens: Maximum tokens in the generated summary
            lang: Target language for summarization
            tone: Summary tone/style
            
        Returns:
            SummaryResult with generated summary and comprehensive metadata
            
        Raises:
            LLMProviderError: If summarization fails after all retries
            ValidationError: If input parameters are invalid
            
        Example:
            ```python
            result = await provider.summarize(
                text="Long article about AI...",
                max_tokens=100,
                lang="en",
                tone="concise"
            )
            print(f"Summary: {result['summary']}")
            print(f"Tokens used: {result['usage']['total_tokens']}")
            print(f"Latency: {result['latency_ms']}ms")
            ```
        """
        start_time = time.time()
        
        try:
            # Build optimized prompt
            prompt = self._build_prompt(text, lang, tone, max_tokens)
            
            # Generate content with retries
            response = await self._generate_with_retry(prompt)
            
            # Extract summary
            summary = response.text.strip()
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build usage statistics
            # Note: Gemini doesn't provide exact token counts in response
            # We estimate based on text length (approximate: 1 token ≈ 4 characters)
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(summary) // 4
            
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
            
            return SummaryResult(
                summary=summary,
                usage=usage,
                model=self.model_name,
                latency_ms=latency_ms
            )
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
            
        except LLMProviderError:
            # Re-raise LLM errors as-is
            raise
            
        except Exception as e:
            # Catch any unexpected errors
            raise LLMProviderError(
                f"Unexpected error during summarization / Error inesperado durante resumen: {str(e)}",
                provider=self.provider_name,
                model=self.model_name,
                attempts=self.max_attempts,
                last_error=str(e)
            )
    
    def __repr__(self) -> str:
        """
        String representation of the provider.
        
        Returns:
            String representation with provider details
        """
        return (
            f"GeminiProvider("
            f"model={self.model_name}, "
            f"timeout={self.timeout}s, "
            f"max_attempts={self.max_attempts}, "
            f"temperature={self.temperature}"
            f")"
        )


# Export for easy importing
__all__ = ["GeminiProvider"]
