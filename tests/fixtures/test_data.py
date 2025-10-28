"""
Test data fixtures and sample data.

Provides comprehensive test data for all testing scenarios
including sample texts, mock responses, and expected results.
"""

from typing import Dict, Any, List


# Sample texts for testing
SAMPLE_TEXTS = {
    "short": "This is a short text for testing.",
    "medium": """
    Artificial intelligence is revolutionizing industries across the globe. 
    From healthcare to finance, AI technologies are enabling unprecedented 
    levels of automation and efficiency. Machine learning algorithms can 
    now process vast amounts of data to identify patterns and make predictions 
    with remarkable accuracy. However, this rapid advancement also brings 
    challenges related to ethics, privacy, and job displacement that society 
    must address carefully.
    """,
    "long": """
    The rapid advancement of artificial intelligence and machine learning 
    technologies has fundamentally transformed the way we approach complex 
    problems across multiple domains. In healthcare, AI-powered diagnostic 
    tools are helping doctors identify diseases earlier and more accurately 
    than ever before. Machine learning algorithms can analyze medical images, 
    patient records, and genetic data to provide personalized treatment 
    recommendations that improve patient outcomes.
    
    In the financial sector, AI is revolutionizing risk assessment, fraud 
    detection, and algorithmic trading. Banks and financial institutions 
    are using machine learning models to analyze customer behavior patterns, 
    detect suspicious transactions, and optimize investment strategies. 
    These applications not only improve efficiency but also enhance security 
    and reduce financial risks.
    
    The transportation industry has also been significantly impacted by AI 
    developments. Autonomous vehicles powered by sophisticated AI systems 
    promise to reduce traffic accidents, improve fuel efficiency, and 
    transform urban mobility. Companies like Tesla, Google, and traditional 
    automakers are investing heavily in self-driving technology that relies 
    on computer vision, sensor fusion, and decision-making algorithms.
    
    However, the widespread adoption of AI also presents significant challenges. 
    Ethical considerations around bias in AI systems, privacy concerns related 
    to data collection and processing, and the potential displacement of 
    human workers are critical issues that need to be addressed. As AI 
    becomes more powerful and ubiquitous, society must develop frameworks 
    for responsible AI development and deployment.
    """,
    "multilingual": {
        "english": "The quick brown fox jumps over the lazy dog.",
        "spanish": "El zorro marrón rápido salta sobre el perro perezoso.",
        "french": "Le renard brun rapide saute par-dessus le chien paresseux.",
        "german": "Der schnelle braune Fuchs springt über den faulen Hund."
    }
}


# Mock API responses
MOCK_GEMINI_RESPONSE = {
    "summary": "AI is transforming industries globally through automation and efficiency. Machine learning enables data processing and predictions, but raises ethical and privacy concerns.",
    "usage": {
        "prompt_tokens": 120,
        "completion_tokens": 40,
        "total_tokens": 160
    },
    "model": "gemini-pro",
    "latency_ms": 1250
}


MOCK_FALLBACK_RESPONSE = {
    "summary": "Artificial intelligence is revolutionizing industries. Machine learning algorithms process data efficiently. Challenges include ethics and privacy.",
    "usage": {
        "prompt_tokens": 80,
        "completion_tokens": 25,
        "total_tokens": 105
    },
    "model": "textrank-extractive",
    "latency_ms": 500
}


# Mock evaluation metrics
MOCK_EVALUATION_METRICS = {
    "rouge_1_f": 0.75,
    "rouge_2_f": 0.65,
    "rouge_l_f": 0.70,
    "semantic_similarity": 0.85,
    "compression_ratio": 0.20,
    "quality_score": 0.78
}


# Mock health check responses
MOCK_HEALTH_RESPONSES = {
    "healthy": {
        "status": "healthy",
        "timestamp": 1640995200.123,
        "services": {
            "llm_provider": {
                "status": "healthy",
                "response_time_ms": 150,
                "details": {"model": "gemini-pro"}
            },
            "redis": {
                "status": "healthy",
                "response_time_ms": 5,
                "details": {"connected_clients": 10}
            }
        },
        "version": "1.0.0",
        "uptime_seconds": 86400.0
    },
    "degraded": {
        "status": "degraded",
        "timestamp": 1640995200.123,
        "services": {
            "llm_provider": {
                "status": "healthy",
                "response_time_ms": 150
            },
            "redis": {
                "status": "unhealthy",
                "response_time_ms": 5000,
                "error": "Connection timeout"
            }
        },
        "version": "1.0.0",
        "uptime_seconds": 86400.0
    },
    "unhealthy": {
        "status": "unhealthy",
        "timestamp": 1640995200.123,
        "services": {
            "llm_provider": {
                "status": "unhealthy",
                "response_time_ms": 10000,
                "error": "API key invalid"
            },
            "redis": {
                "status": "unhealthy",
                "response_time_ms": 5000,
                "error": "Connection refused"
            }
        },
        "version": "1.0.0",
        "uptime_seconds": 86400.0
    }
}


# Test request data
TEST_REQUESTS = {
    "valid": {
        "text": SAMPLE_TEXTS["medium"],
        "lang": "en",
        "max_tokens": 100,
        "tone": "neutral"
    },
    "minimal": {
        "text": SAMPLE_TEXTS["short"],
        "lang": "auto",
        "max_tokens": 50,
        "tone": "concise"
    },
    "maximal": {
        "text": SAMPLE_TEXTS["long"],
        "lang": "en",
        "max_tokens": 500,
        "tone": "bullet"
    },
    "multilingual": {
        "text": SAMPLE_TEXTS["multilingual"]["spanish"],
        "lang": "es",
        "max_tokens": 100,
        "tone": "neutral"
    }
}


# Invalid request data for testing validation
INVALID_REQUESTS = {
    "empty_text": {
        "text": "",
        "lang": "en",
        "max_tokens": 100,
        "tone": "neutral"
    },
    "text_too_short": {
        "text": "Hi",
        "lang": "en",
        "max_tokens": 100,
        "tone": "neutral"
    },
    "text_too_long": {
        "text": "x" * 50001,
        "lang": "en",
        "max_tokens": 100,
        "tone": "neutral"
    },
    "invalid_language": {
        "text": SAMPLE_TEXTS["short"],
        "lang": "invalid_lang",
        "max_tokens": 100,
        "tone": "neutral"
    },
    "invalid_tone": {
        "text": SAMPLE_TEXTS["short"],
        "lang": "en",
        "max_tokens": 100,
        "tone": "invalid_tone"
    },
    "max_tokens_too_low": {
        "text": SAMPLE_TEXTS["short"],
        "lang": "en",
        "max_tokens": 5,
        "tone": "neutral"
    },
    "max_tokens_too_high": {
        "text": SAMPLE_TEXTS["short"],
        "lang": "en",
        "max_tokens": 1000,
        "tone": "neutral"
    }
}


# Error scenarios
ERROR_SCENARIOS = {
    "gemini_api_error": {
        "error_type": "LLMProviderError",
        "message": "Gemini API error / Error de API de Gemini",
        "status_code": 503
    },
    "cache_error": {
        "error_type": "CacheError",
        "message": "Cache operation failed / Operación de cache falló",
        "status_code": 500
    },
    "evaluation_error": {
        "error_type": "EvaluationError",
        "message": "Evaluation failed / Evaluación falló",
        "status_code": 500
    },
    "validation_error": {
        "error_type": "ValidationError",
        "message": "Invalid input / Entrada inválida",
        "status_code": 400
    },
    "rate_limit_error": {
        "error_type": "RateLimitExceededError",
        "message": "Rate limit exceeded / Límite de velocidad excedido",
        "status_code": 429
    },
    "auth_error": {
        "error_type": "AuthenticationError",
        "message": "Invalid API key / Clave API inválida",
        "status_code": 401
    }
}


# Performance test data
PERFORMANCE_TEST_DATA = {
    "small_text": SAMPLE_TEXTS["short"],
    "medium_text": SAMPLE_TEXTS["medium"],
    "large_text": SAMPLE_TEXTS["long"],
    "expected_latency_ranges": {
        "small": (100, 1000),  # ms
        "medium": (500, 2000),
        "large": (1000, 5000)
    }
}


# Cache test data
CACHE_TEST_DATA = {
    "cache_key": "test_cache_key",
    "cache_value": MOCK_GEMINI_RESPONSE,
    "ttl": 3600,
    "namespace": "test_namespace"
}


# Rate limiting test data
RATE_LIMIT_TEST_DATA = {
    "limit": 100,
    "window": 60,
    "test_requests": 150,  # More than limit
    "expected_remaining": 0,
    "expected_reset_time": None  # Will be calculated
}


# Export all test data
__all__ = [
    "SAMPLE_TEXTS",
    "MOCK_GEMINI_RESPONSE",
    "MOCK_FALLBACK_RESPONSE", 
    "MOCK_EVALUATION_METRICS",
    "MOCK_HEALTH_RESPONSES",
    "TEST_REQUESTS",
    "INVALID_REQUESTS",
    "ERROR_SCENARIOS",
    "PERFORMANCE_TEST_DATA",
    "CACHE_TEST_DATA",
    "RATE_LIMIT_TEST_DATA",
]
