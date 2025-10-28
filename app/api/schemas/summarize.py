"""
Pydantic schemas for summarization API endpoints.

Defines request and response models with comprehensive validation,
detailed documentation, and examples for OpenAPI generation.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, validator

from app.core.constants import (
    MIN_TEXT_LENGTH,
    MAX_TEXT_LENGTH,
    MIN_SUMMARY_TOKENS,
    MAX_SUMMARY_TOKENS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_TONES,
)


class SummarizeRequest(BaseModel):
    """
    Request model for text summarization.
    
    Validates input parameters for text summarization with comprehensive
    validation rules and detailed documentation for API consumers.
    
    Attributes:
        text: Input text to summarize (10-50,000 characters)
        lang: Target language for summarization
        max_tokens: Maximum tokens in generated summary
        tone: Summary style/tone
    """
    
    text: str = Field(
        ...,
        min_length=MIN_TEXT_LENGTH,
        max_length=MAX_TEXT_LENGTH,
        description="Text to summarize. Must be between 10 and 50,000 characters.",
        examples=[
            "Artificial intelligence is transforming industries worldwide...",
            "The rapid advancement of machine learning technologies...",
            "Climate change represents one of the greatest challenges..."
        ]
    )
    
    lang: str = Field(
        default="auto",
        description="Target language for summarization. Use 'auto' for automatic detection.",
        examples=["auto", "en", "es", "fr", "de"]
    )
    
    max_tokens: int = Field(
        default=100,
        ge=MIN_SUMMARY_TOKENS,
        le=MAX_SUMMARY_TOKENS,
        description=f"Maximum tokens in the generated summary. Range: {MIN_SUMMARY_TOKENS}-{MAX_SUMMARY_TOKENS}",
        examples=[50, 100, 200, 300]
    )
    
    tone: Literal["neutral", "concise", "bullet"] = Field(
        default="neutral",
        description="Summary style and tone. 'neutral' for balanced, 'concise' for brief, 'bullet' for structured points.",
        examples=["neutral", "concise", "bullet"]
    )
    
    @validator('text')
    def validate_text_content(cls, v):
        """
        Validate text content quality.
        
        Ensures text has sufficient content for meaningful summarization
        by checking word count and content quality.
        
        Args:
            v: Text content to validate
            
        Returns:
            Validated text content
            
        Raises:
            ValueError: If text quality is insufficient
        """
        if not v or not v.strip():
            raise ValueError("Text cannot be empty / Texto no puede estar vacío")
        
        # Check word count
        word_count = len(v.split())
        if word_count < 5:
            raise ValueError(
                f"Text too short ({word_count} words). Minimum 5 words required / "
                f"Texto muy corto ({word_count} palabras). Mínimo 5 palabras requeridas"
            )
        
        # Check for meaningful content (not just repeated characters)
        unique_chars = len(set(v.lower()))
        if unique_chars < 3:
            raise ValueError(
                "Text appears to contain insufficient meaningful content / "
                "El texto parece contener contenido insuficientemente significativo"
            )
        
        return v.strip()
    
    @validator('lang')
    def validate_language(cls, v):
        """
        Validate language code.
        
        Ensures the language code is supported by the summarization service.
        
        Args:
            v: Language code to validate
            
        Returns:
            Validated language code
            
        Raises:
            ValueError: If language is not supported
        """
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{v}'. Supported: {', '.join(SUPPORTED_LANGUAGES)} / "
                f"Idioma no soportado '{v}'. Soportados: {', '.join(SUPPORTED_LANGUAGES)}"
            )
        return v
    
    @validator('tone')
    def validate_tone(cls, v):
        """
        Validate tone parameter.
        
        Ensures the tone parameter is valid and supported.
        
        Args:
            v: Tone parameter to validate
            
        Returns:
            Validated tone parameter
            
        Raises:
            ValueError: If tone is not supported
        """
        if v not in SUPPORTED_TONES:
            raise ValueError(
                f"Unsupported tone '{v}'. Supported: {', '.join(SUPPORTED_TONES)} / "
                f"Tono no soportado '{v}'. Soportados: {', '.join(SUPPORTED_TONES)}"
            )
        return v
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "text": "Artificial intelligence is revolutionizing industries across the globe. From healthcare to finance, AI technologies are enabling unprecedented levels of automation and efficiency. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions with remarkable accuracy. However, this rapid advancement also brings challenges related to ethics, privacy, and job displacement that society must address.",
                "lang": "en",
                "max_tokens": 100,
                "tone": "neutral"
            }
        }


class TokenUsage(BaseModel):
    """
    Token usage statistics for summarization.
    
    Provides detailed information about token consumption during
    the summarization process for monitoring and billing purposes.
    
    Attributes:
        prompt_tokens: Tokens used in the input prompt
        completion_tokens: Tokens generated in the summary
        total_tokens: Total tokens used
    """
    
    prompt_tokens: int = Field(
        ...,
        ge=0,
        description="Number of tokens used in the input prompt",
        example=120
    )
    
    completion_tokens: int = Field(
        ...,
        ge=0,
        description="Number of tokens generated in the summary",
        example=40
    )
    
    total_tokens: int = Field(
        ...,
        ge=0,
        description="Total number of tokens used (prompt + completion)",
        example=160
    )


class EvaluationMetrics(BaseModel):
    """
    Quality evaluation metrics for generated summaries.
    
    Provides comprehensive quality assessment using multiple
    evaluation methods including ROUGE scores and semantic similarity.
    
    Attributes:
        rouge_1_f: ROUGE-1 F-score (unigram overlap)
        rouge_2_f: ROUGE-2 F-score (bigram overlap)
        rouge_l_f: ROUGE-L F-score (longest common subsequence)
        semantic_similarity: Cosine similarity between embeddings
        compression_ratio: Ratio of summary length to original length
        quality_score: Weighted composite quality score
    """
    
    rouge_1_f: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="ROUGE-1 F-score measuring unigram overlap",
        example=0.75
    )
    
    rouge_2_f: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="ROUGE-2 F-score measuring bigram overlap",
        example=0.65
    )
    
    rouge_l_f: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="ROUGE-L F-score measuring longest common subsequence",
        example=0.70
    )
    
    semantic_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity between original text and summary embeddings",
        example=0.85
    )
    
    compression_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of summary length to original text length",
        example=0.20
    )
    
    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted composite quality score (0-1)",
        example=0.78
    )


class SummarizeResponse(BaseModel):
    """
    Response model for text summarization.
    
    Provides comprehensive response information including the generated
    summary, usage statistics, model information, and optional quality metrics.
    
    Attributes:
        summary: Generated summary text
        usage: Token usage statistics
        model: Model identifier used for generation
        latency_ms: Processing time in milliseconds
        evaluation: Optional quality evaluation metrics
        cached: Whether result was served from cache
    """
    
    summary: str = Field(
        ...,
        description="Generated summary text",
        example="AI is transforming industries globally through automation and efficiency. Machine learning enables data processing and predictions, but raises ethical and privacy concerns."
    )
    
    usage: TokenUsage = Field(
        ...,
        description="Token usage statistics for the summarization process"
    )
    
    model: str = Field(
        ...,
        description="Model identifier used for generating the summary",
        examples=["gemini-pro", "textrank-extractive"]
    )
    
    latency_ms: int = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds",
        example=1250
    )
    
    evaluation: Optional[EvaluationMetrics] = Field(
        None,
        description="Quality evaluation metrics (included if auto-evaluation is enabled)"
    )
    
    cached: bool = Field(
        False,
        description="Whether this result was served from cache",
        example=False
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "summary": "AI is transforming industries globally through automation and efficiency. Machine learning enables data processing and predictions, but raises ethical and privacy concerns.",
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 40,
                    "total_tokens": 160
                },
                "model": "gemini-pro",
                "latency_ms": 1250,
                "evaluation": {
                    "rouge_1_f": 0.75,
                    "rouge_2_f": 0.65,
                    "rouge_l_f": 0.70,
                    "semantic_similarity": 0.85,
                    "compression_ratio": 0.20,
                    "quality_score": 0.78
                },
                "cached": False
            }
        }


# Export for easy importing
__all__ = [
    "SummarizeRequest",
    "SummarizeResponse", 
    "TokenUsage",
    "EvaluationMetrics",
]
