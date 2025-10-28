"""
Extractive summarization fallback provider using TextRank algorithm.

Provides reliable extractive summarization as a fallback when LLM providers
fail, ensuring the service always returns a summary even during outages.
Uses the TextRank algorithm via the sumy library for high-quality extraction.
"""

import time
from typing import Literal

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from app.core.constants import (
    FALLBACK_PROVIDER,
    SIMPLE_FALLBACK_PROVIDER,
    SUPPORTED_LANGUAGES,
    SUPPORTED_TONES,
    MIN_SUMMARY_TOKENS,
    MAX_SUMMARY_TOKENS,
)
from app.core.exceptions import ValidationError, LLMProviderError
from app.providers.base import BaseLLMProvider, SummaryResult


class ExtractiveFallbackProvider(BaseLLMProvider):
    """
    Extractive summarization fallback using TextRank algorithm.
    
    Provides reliable extractive summarization as a fallback when LLM
    providers fail. Uses the TextRank algorithm via the sumy library
    to extract the most important sentences from the input text.
    
    Features:
    - TextRank algorithm for high-quality sentence extraction
    - Support for multiple languages with appropriate tokenizers
    - Tone-based formatting (neutral, concise, bullet points)
    - Automatic sentence count calculation based on token limits
    - Comprehensive error handling with graceful degradation
    - No external API dependencies (fully local processing)
    
    Attributes:
        default_sentences: Default number of sentences to extract
        min_sentences: Minimum sentences to extract
        max_sentences: Maximum sentences to extract
    """
    
    def __init__(
        self,
        default_sentences: int = 3,
        min_sentences: int = 1,
        max_sentences: int = 10
    ):
        """
        Initialize extractive summarizer.
        
        Sets up the TextRank summarizer with appropriate configuration
        for reliable extractive summarization across different languages.
        
        Args:
            default_sentences: Default number of sentences to extract
            min_sentences: Minimum sentences to extract
            max_sentences: Maximum sentences to extract
            
        Raises:
            ValidationError: If sentence limits are invalid
            
        Example:
            ```python
            provider = ExtractiveFallbackProvider(
                default_sentences=3,
                min_sentences=1,
                max_sentences=8
            )
            ```
        """
        # Validate sentence limits
        if min_sentences < 1:
            raise ValidationError(
                "Minimum sentences must be at least 1 / Mínimo de oraciones debe ser al menos 1",
                field="min_sentences",
                value=min_sentences
            )
        
        if max_sentences < min_sentences:
            raise ValidationError(
                f"Maximum sentences ({max_sentences}) must be >= minimum ({min_sentences}) / "
                f"Máximo de oraciones ({max_sentences}) debe ser >= mínimo ({min_sentences})",
                field="max_sentences",
                value=max_sentences
            )
        
        if default_sentences < min_sentences or default_sentences > max_sentences:
            raise ValidationError(
                f"Default sentences ({default_sentences}) must be between min ({min_sentences}) and max ({max_sentences}) / "
                f"Oraciones por defecto ({default_sentences}) debe estar entre min ({min_sentences}) y max ({max_sentences})",
                field="default_sentences",
                value=default_sentences
            )
        
        self.default_sentences = default_sentences
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences
    
    @property
    def provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            Provider name identifier
        """
        return FALLBACK_PROVIDER
    
    @property
    def model_name(self) -> str:
        """
        Get the model name.
        
        Returns:
            Model name identifier
        """
        return "textrank-extractive"
    
    def _get_language_code(self, lang: str) -> str:
        """
        Map language to NLTK language code.
        
        Maps supported language codes to NLTK language identifiers
        used by the sumy library for tokenization and stemming.
        
        Args:
            lang: Language code from request
            
        Returns:
            NLTK language code
            
        Raises:
            ValidationError: If language is not supported
        """
        lang_map = {
            "auto": "english",  # Default to English
            "en": "english",
            "es": "spanish",
            "fr": "french",
            "de": "german",
            "it": "italian",
            "pt": "portuguese",
            "ru": "russian",
            "zh": "chinese",
            "ja": "japanese",
            "ko": "korean",
        }
        
        if lang not in lang_map:
            raise ValidationError(
                f"Unsupported language '{lang}' for extractive summarization / "
                f"Idioma no soportado '{lang}' para resumen extractivo",
                field="lang",
                value=lang,
                details={"supported_languages": list(lang_map.keys())}
            )
        
        return lang_map[lang]
    
    def _calculate_sentence_count(self, text: str, max_tokens: int) -> int:
        """
        Calculate optimal number of sentences based on token limit.
        
        Estimates the number of sentences to extract based on the
        maximum token limit, using average sentence length estimates.
        
        Args:
            text: Input text to analyze
            max_tokens: Maximum tokens allowed in summary
            
        Returns:
            Optimal number of sentences to extract
        """
        # Count sentences in text
        sentences = text.split('. ')
        total_sentences = len(sentences)
        
        if total_sentences == 0:
            return self.min_sentences
        
        # Estimate average tokens per sentence (approximate: 1 token ≈ 4 characters)
        avg_chars_per_sentence = len(text) / total_sentences
        avg_tokens_per_sentence = avg_chars_per_sentence / 4
        
        # Calculate sentences needed for target tokens
        target_sentences = max(1, int(max_tokens / avg_tokens_per_sentence))
        
        # Apply limits
        target_sentences = max(self.min_sentences, min(target_sentences, self.max_sentences))
        target_sentences = min(target_sentences, total_sentences)
        
        return target_sentences
    
    def _format_summary(self, sentences: list[str], tone: str) -> str:
        """
        Format extracted sentences based on requested tone.
        
        Applies tone-specific formatting to the extracted sentences
        to match the requested style (neutral, concise, bullet).
        
        Args:
            sentences: List of extracted sentences
            tone: Requested tone for formatting
            
        Returns:
            Formatted summary string
        """
        if tone == "bullet":
            # Format as bullet points
            formatted_sentences = [f"• {sentence.strip()}" for sentence in sentences]
            return "\n".join(formatted_sentences)
        
        elif tone == "concise":
            # Join with minimal punctuation for concise style
            return ". ".join(sentence.strip() for sentence in sentences) + "."
        
        else:  # neutral
            # Standard formatting
            return ". ".join(sentence.strip() for sentence in sentences) + "."
    
    async def summarize(
        self,
        text: str,
        *,
        max_tokens: int,
        lang: str,
        tone: str
    ) -> SummaryResult:
        """
        Generate extractive summary using TextRank algorithm.
        
        Extracts the most important sentences from the input text using
        the TextRank algorithm. Provides reliable summarization without
        requiring external API calls, making it perfect as a fallback
        when LLM providers fail.
        
        Args:
            text: Input text to summarize
            max_tokens: Maximum tokens in the generated summary
            lang: Target language for summarization
            tone: Summary tone/style
            
        Returns:
            SummaryResult with extracted summary and metadata
            
        Raises:
            ValidationError: If parameters are invalid
            LLMProviderError: If summarization fails completely
            
        Example:
            ```python
            result = await provider.summarize(
                text="Long article text...",
                max_tokens=100,
                lang="en",
                tone="bullet"
            )
            print(f"Extracted summary: {result['summary']}")
            ```
        """
        start_time = time.time()
        
        try:
            # Validate parameters
            if lang not in SUPPORTED_LANGUAGES:
                raise ValidationError(
                    f"Unsupported language '{lang}' / Idioma no soportado '{lang}'",
                    field="lang",
                    value=lang,
                    details={"supported_languages": SUPPORTED_LANGUAGES}
                )
            
            if tone not in SUPPORTED_TONES:
                raise ValidationError(
                    f"Unsupported tone '{tone}' / Tono no soportado '{tone}'",
                    field="tone",
                    value=tone,
                    details={"supported_tones": SUPPORTED_TONES}
                )
            
            if max_tokens < MIN_SUMMARY_TOKENS or max_tokens > MAX_SUMMARY_TOKENS:
                raise ValidationError(
                    f"Max tokens must be between {MIN_SUMMARY_TOKENS}-{MAX_SUMMARY_TOKENS} / "
                    f"Máximo de tokens debe estar entre {MIN_SUMMARY_TOKENS}-{MAX_SUMMARY_TOKENS}",
                    field="max_tokens",
                    value=max_tokens
                )
            
            # Calculate optimal sentence count
            num_sentences = self._calculate_sentence_count(text, max_tokens)
            
            # Get language configuration
            language_code = self._get_language_code(lang)
            
            # Parse text
            parser = PlaintextParser.from_string(
                text,
                Tokenizer(language_code)
            )
            
            # Initialize TextRank summarizer
            stemmer = Stemmer(language_code)
            summarizer = TextRankSummarizer(stemmer)
            summarizer.stop_words = get_stop_words(language_code)
            
            # Generate summary
            sentences = summarizer(parser.document, num_sentences)
            
            # Convert to strings and format
            sentence_strings = [str(sentence) for sentence in sentences]
            summary = self._format_summary(sentence_strings, tone)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Build usage statistics (approximate)
            prompt_tokens = len(text.split())
            completion_tokens = len(summary.split())
            
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
            
        except Exception as e:
            # Fallback to simple extraction if TextRank fails
            try:
                return await self._simple_fallback(text, max_tokens, tone, start_time)
            except Exception as fallback_error:
                raise LLMProviderError(
                    f"Extractive summarization failed / Resumen extractivo falló: {str(e)}. "
                    f"Fallback also failed / Fallback también falló: {str(fallback_error)}",
                    provider=self.provider_name,
                    model=self.model_name,
                    last_error=str(e)
                )
    
    async def _simple_fallback(
        self,
        text: str,
        max_tokens: int,
        tone: str,
        start_time: float
    ) -> SummaryResult:
        """
        Simple fallback extraction when TextRank fails.
        
        Provides a basic sentence extraction as ultimate fallback
        when the TextRank algorithm fails completely.
        
        Args:
            text: Input text
            max_tokens: Maximum tokens
            tone: Summary tone
            start_time: Start time for latency calculation
            
        Returns:
            SummaryResult with simple extraction
        """
        # Simple sentence extraction
        sentences = text.split('. ')
        
        # Calculate how many sentences to take
        avg_chars_per_sentence = len(text) / max(len(sentences), 1)
        avg_tokens_per_sentence = avg_chars_per_sentence / 4
        num_sentences = max(1, min(int(max_tokens / avg_tokens_per_sentence), len(sentences)))
        
        # Take first N sentences
        selected_sentences = sentences[:num_sentences]
        summary = self._format_summary(selected_sentences, tone)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build usage statistics
        prompt_tokens = len(text.split())
        completion_tokens = len(summary.split())
        
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
        
        return SummaryResult(
            summary=summary,
            usage=usage,
            model=SIMPLE_FALLBACK_PROVIDER,
            latency_ms=latency_ms
        )
    
    def __repr__(self) -> str:
        """
        String representation of the provider.
        
        Returns:
            String representation with provider details
        """
        return (
            f"ExtractiveFallbackProvider("
            f"default_sentences={self.default_sentences}, "
            f"min_sentences={self.min_sentences}, "
            f"max_sentences={self.max_sentences}"
            f")"
        )


# Export for easy importing
__all__ = ["ExtractiveFallbackProvider"]
