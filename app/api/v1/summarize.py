"""
Summarization API router.

Provides the main summarization endpoint with comprehensive
validation, caching, fallback handling, and quality evaluation.
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.api.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.core.dependencies import ApiKeyDep, ApiKeyHashDep, SettingsDep
from app.core.exceptions import (
    ValidationError,
    LLMProviderError,
    CacheError,
    EvaluationError,
)
from app.providers.llm.gemini import GeminiProvider
from app.providers.llm.fallback import ExtractiveFallbackProvider
from app.services.evaluation import SummaryEvaluator
from app.services.cache import CacheService
from app.config import Settings

logger = structlog.get_logger()

router = APIRouter()


async def get_llm_provider(settings: SettingsDep) -> GeminiProvider:
    """
    Get LLM provider instance.
    
    Creates and returns a configured Gemini provider instance
    with appropriate settings and error handling.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured GeminiProvider instance
        
    Raises:
        HTTPException: If provider initialization fails
    """
    try:
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_ms // 1000,
            max_attempts=3
        )
    except Exception as e:
        logger.error(
            "llm_provider_init_failed",
            error=str(e),
            model=settings.gemini_model
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider initialization failed / Error al inicializar proveedor LLM"
        )


async def get_fallback_provider() -> ExtractiveFallbackProvider:
    """
    Get fallback provider instance.
    
    Creates and returns a configured extractive fallback provider
    for use when LLM providers fail.
    
    Returns:
        Configured ExtractiveFallbackProvider instance
    """
    return ExtractiveFallbackProvider(
        default_sentences=3,
        min_sentences=1,
        max_sentences=8
    )


async def get_evaluator(settings: SettingsDep) -> Optional[SummaryEvaluator]:
    """
    Get evaluation service instance.
    
    Creates and returns a configured evaluation service if
    auto-evaluation is enabled in settings.
    
    Args:
        settings: Application settings
        
    Returns:
        SummaryEvaluator instance or None if disabled
    """
    if not settings.enable_auto_evaluation:
        return None
    
    try:
        return SummaryEvaluator(model_name=settings.evaluation_model)
    except Exception as e:
        logger.warning(
            "evaluator_init_failed",
            error=str(e),
            model=settings.evaluation_model
        )
        return None


async def get_cache_service(settings: SettingsDep) -> Optional[CacheService]:
    """
    Get cache service instance.
    
    Creates and returns a configured cache service if
    Redis is available and configured.
    
    Args:
        settings: Application settings
        
    Returns:
        CacheService instance or None if unavailable
    """
    try:
        return CacheService(
            redis_url=settings.redis_url,
            ttl_seconds=settings.cache_ttl_seconds,
            namespace="summaries"
        )
    except Exception as e:
        logger.warning(
            "cache_service_init_failed",
            error=str(e),
            redis_url=settings.redis_url
        )
        return None


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Summarize text using AI",
    description="""
    Generate a high-quality summary of the provided text using advanced AI models.
    
    **Features:**
    - Support for multiple languages (auto-detection available)
    - Configurable summary length and tone
    - Automatic fallback to extractive summarization if AI fails
    - Optional quality evaluation with ROUGE scores and semantic similarity
    - Intelligent caching for improved performance
    
    **Parameters:**
    - **text**: Input text to summarize (10-50,000 characters)
    - **lang**: Target language (auto, en, es, fr, de, etc.)
    - **max_tokens**: Maximum tokens in summary (10-500)
    - **tone**: Summary style (neutral, concise, bullet)
    
    **Response includes:**
    - Generated summary
    - Token usage statistics
    - Model information
    - Processing time
    - Optional quality metrics
    """,
    responses={
        200: {
            "description": "Summary generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "summary": "AI is transforming industries globally through automation and efficiency.",
                        "usage": {"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
                        "model": "gemini-pro",
                        "latency_ms": 1250,
                        "evaluation": {"quality_score": 0.78},
                        "cached": False
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Service temporarily unavailable"}
    },
    tags=["Summarization"]
)
async def summarize_text(
    request: SummarizeRequest,
    api_key: ApiKeyDep,
    api_key_hash: ApiKeyHashDep,
    settings: SettingsDep,
    llm_provider: GeminiProvider = Depends(get_llm_provider),
    fallback_provider: ExtractiveFallbackProvider = Depends(get_fallback_provider),
    evaluator: Optional[SummaryEvaluator] = Depends(get_evaluator),
    cache_service: Optional[CacheService] = Depends(get_cache_service)
) -> SummarizeResponse:
    """
    Summarize text using AI with comprehensive error handling and fallback.
    
    This endpoint provides high-quality text summarization using advanced AI models
    with automatic fallback to extractive summarization if needed. Includes
    intelligent caching, quality evaluation, and comprehensive error handling.
    
    Args:
        request: Summarization request with text and parameters
        api_key: Validated API key
        api_key_hash: Anonymized API key hash for logging
        settings: Application settings
        llm_provider: Configured LLM provider
        fallback_provider: Fallback extractive provider
        evaluator: Optional quality evaluator
        cache_service: Optional cache service
        
    Returns:
        SummarizeResponse with generated summary and metadata
        
    Raises:
        HTTPException: For various error conditions
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        "summarize_request_started",
        api_key_hash=api_key_hash,
        text_length=len(request.text),
        lang=request.lang,
        max_tokens=request.max_tokens,
        tone=request.tone
    )
    
    try:
        # Check cache first
        cached_result = None
        if cache_service:
            try:
                cache_params = {
                    "lang": request.lang,
                    "max_tokens": request.max_tokens,
                    "tone": request.tone
                }
                cached_result = await cache_service.get(request.text, cache_params)
                
                if cached_result:
                    logger.info(
                        "cache_hit",
                        api_key_hash=api_key_hash,
                        text_length=len(request.text)
                    )
                    
                    # Add current timestamp for latency
                    cached_result["latency_ms"] = int((time.time() - start_time) * 1000)
                    cached_result["cached"] = True
                    
                    return SummarizeResponse(**cached_result)
                    
            except Exception as e:
                logger.warning(
                    "cache_get_failed",
                    error=str(e),
                    api_key_hash=api_key_hash
                )
        
        # Generate summary using LLM provider
        try:
            result = await llm_provider.summarize(
                text=request.text,
                max_tokens=request.max_tokens,
                lang=request.lang,
                tone=request.tone
            )
            
            logger.info(
                "llm_summary_generated",
                api_key_hash=api_key_hash,
                model=result["model"],
                latency_ms=result["latency_ms"]
            )
            
        except Exception as e:
            logger.warning(
                "llm_provider_failed",
                error=str(e),
                api_key_hash=api_key_hash
            )
            
            # Use fallback provider
            try:
                result = await fallback_provider.summarize(
                    text=request.text,
                    max_tokens=request.max_tokens,
                    lang=request.lang,
                    tone=request.tone
                )
                
                logger.info(
                    "fallback_summary_generated",
                    api_key_hash=api_key_hash,
                    model=result["model"],
                    latency_ms=result["latency_ms"]
                )
                
            except Exception as fallback_error:
                logger.error(
                    "fallback_provider_failed",
                    error=str(fallback_error),
                    api_key_hash=api_key_hash
                )
                
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Summarization service temporarily unavailable / Servicio de resumen temporalmente no disponible"
                )
        
        # Evaluate quality if evaluator is available
        evaluation = None
        if evaluator:
            try:
                evaluation = evaluator.evaluate(request.text, result["summary"])
                
                logger.info(
                    "quality_evaluation_completed",
                    api_key_hash=api_key_hash,
                    quality_score=evaluation["quality_score"]
                )
                
            except Exception as e:
                logger.warning(
                    "quality_evaluation_failed",
                    error=str(e),
                    api_key_hash=api_key_hash
                )
        
        # Build response
        response_data = {
            "summary": result["summary"],
            "usage": result["usage"],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "evaluation": evaluation,
            "cached": False
        }
        
        # Cache result if cache service is available
        if cache_service and not cached_result:
            try:
                await cache_service.set(
                    text=request.text,
                    params={
                        "lang": request.lang,
                        "max_tokens": request.max_tokens,
                        "tone": request.tone
                    },
                    result=response_data
                )
                
                logger.info(
                    "result_cached",
                    api_key_hash=api_key_hash,
                    text_length=len(request.text)
                )
                
            except Exception as e:
                logger.warning(
                    "cache_set_failed",
                    error=str(e),
                    api_key_hash=api_key_hash
                )
        
        # Log successful completion
        logger.info(
            "summarize_request_completed",
            api_key_hash=api_key_hash,
            model=result["model"],
            latency_ms=result["latency_ms"],
            cached=False
        )
        
        return SummarizeResponse(**response_data)
        
    except ValidationError as e:
        logger.warning(
            "validation_error",
            error=str(e),
            api_key_hash=api_key_hash
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except LLMProviderError as e:
        logger.error(
            "llm_provider_error",
            error=str(e),
            api_key_hash=api_key_hash
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Summarization service temporarily unavailable / Servicio de resumen temporalmente no disponible"
        )
        
    except Exception as e:
        logger.exception(
            "unexpected_error",
            error=str(e),
            api_key_hash=api_key_hash
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error / Error interno del servidor"
        )


# Export for easy importing
__all__ = ["router"]
