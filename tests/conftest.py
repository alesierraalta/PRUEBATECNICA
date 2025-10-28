"""
Global pytest fixtures and configuration.

Provides comprehensive fixtures for all test scenarios including
FastAPI test client, mock services, and test data.
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_app
from app.config import Settings
from app.providers.llm.gemini import GeminiProvider
from app.providers.llm.fallback import ExtractiveFallbackProvider
from app.services.cache import CacheService
from app.services.evaluation import SummaryEvaluator

from tests.fixtures.test_data import (
    MOCK_GEMINI_RESPONSE,
    MOCK_FALLBACK_RESPONSE,
    MOCK_EVALUATION_METRICS,
    CACHE_TEST_DATA,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    
    Yields:
        Event loop for async testing
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """
    Create test settings with safe defaults.
    
    Returns:
        Settings instance configured for testing
    """
    return Settings(
        api_keys_allowed="test_api_key_1,test_api_key_2",
        llm_provider="gemini",
        gemini_api_key="test_gemini_key",
        gemini_model="gemini-pro",
        summary_max_tokens=100,
        lang_default="auto",
        request_timeout_ms=10000,
        enable_rate_limit=False,  # Disable for unit tests
        redis_url="redis://localhost:6379/1",  # Test database
        cors_origins=["*"],
        log_level="DEBUG",
        enable_auto_evaluation=True,
        evaluation_model="all-MiniLM-L6-v2",
        cache_ttl_seconds=3600,
        api_title="Test LLM Summarization API",
        api_version="1.0.0-test"
    )


@pytest.fixture
def app(test_settings: Settings):
    """
    Create FastAPI application for testing.
    
    Args:
        test_settings: Test settings
        
    Returns:
        FastAPI application instance
    """
    # Override settings for testing
    import app.config
    app.config._cached_settings = test_settings
    
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """
    Create test client for FastAPI application.
    
    Args:
        app: FastAPI application
        
    Returns:
        TestClient instance
    """
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async test client for FastAPI application.
    
    Args:
        app: FastAPI application
        
    Yields:
        AsyncClient instance
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_gemini_provider(mocker) -> MagicMock:
    """
    Create mock Gemini provider.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock GeminiProvider instance
    """
    mock_provider = mocker.MagicMock(spec=GeminiProvider)
    mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
    return mock_provider


@pytest.fixture
def mock_fallback_provider(mocker) -> MagicMock:
    """
    Create mock fallback provider.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock ExtractiveFallbackProvider instance
    """
    mock_provider = mocker.MagicMock(spec=ExtractiveFallbackProvider)
    mock_provider.summarize = AsyncMock(return_value=MOCK_FALLBACK_RESPONSE)
    return mock_provider


@pytest.fixture
def mock_cache_service(mocker) -> MagicMock:
    """
    Create mock cache service.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock CacheService instance
    """
    mock_cache = mocker.MagicMock(spec=CacheService)
    mock_cache.get = AsyncMock(return_value=None)  # Cache miss by default
    mock_cache.set = AsyncMock(return_value=None)
    mock_cache.delete = AsyncMock(return_value=None)
    mock_cache.get_stats = AsyncMock(return_value={"hits": 0, "misses": 0})
    return mock_cache


@pytest.fixture
def mock_evaluation_service(mocker) -> MagicMock:
    """
    Create mock evaluation service.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock SummaryEvaluator instance
    """
    mock_evaluator = mocker.MagicMock(spec=SummaryEvaluator)
    mock_evaluator.evaluate = MagicMock(return_value=MOCK_EVALUATION_METRICS)
    return mock_evaluator


@pytest.fixture
def valid_api_key() -> str:
    """
    Get valid API key for testing.
    
    Returns:
        Valid API key string
    """
    return "test_api_key_1"


@pytest.fixture
def invalid_api_key() -> str:
    """
    Get invalid API key for testing.
    
    Returns:
        Invalid API key string
    """
    return "invalid_api_key"


@pytest.fixture
def auth_headers(valid_api_key: str) -> dict:
    """
    Create authentication headers for testing.
    
    Args:
        valid_api_key: Valid API key
        
    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {valid_api_key}"}


@pytest.fixture
def invalid_auth_headers(invalid_api_key: str) -> dict:
    """
    Create invalid authentication headers for testing.
    
    Args:
        invalid_api_key: Invalid API key
        
    Returns:
        Dictionary with invalid Authorization header
    """
    return {"Authorization": f"Bearer {invalid_api_key}"}


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Create temporary directory for testing.
    
    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_redis(mocker):
    """
    Mock Redis for testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock Redis instance
    """
    mock_redis = mocker.MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.info = AsyncMock(return_value={"connected_clients": 10})
    return mock_redis


@pytest.fixture
def mock_httpx_client(mocker):
    """
    Mock httpx client for external API calls.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock httpx client
    """
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"candidates": [{"content": {"parts": [{"text": "Test summary"}]}}]})
    mock_response.headers = {"content-type": "application/json"}
    
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_sentence_transformer(mocker):
    """
    Mock SentenceTransformer for evaluation testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock SentenceTransformer instance
    """
    mock_model = mocker.MagicMock()
    mock_model.encode = MagicMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return mock_model


@pytest.fixture
def mock_rouge_scorer(mocker):
    """
    Mock ROUGE scorer for evaluation testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock ROUGE scorer
    """
    mock_scorer = mocker.MagicMock()
    mock_scorer.score = MagicMock(return_value={
        "rouge-1": {"f": 0.75},
        "rouge-2": {"f": 0.65},
        "rouge-l": {"f": 0.70}
    })
    return mock_scorer


@pytest.fixture
def mock_sumy_summarizer(mocker):
    """
    Mock Sumy summarizer for fallback testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock Sumy summarizer
    """
    mock_summarizer = mocker.MagicMock()
    mock_summarizer.summarize = MagicMock(return_value=["Sentence 1", "Sentence 2", "Sentence 3"])
    return mock_summarizer


@pytest.fixture
def mock_networkx_graph(mocker):
    """
    Mock NetworkX graph for TextRank testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock NetworkX graph
    """
    mock_graph = mocker.MagicMock()
    mock_graph.add_edge = MagicMock()
    mock_graph.add_node = MagicMock()
    mock_graph.nodes = MagicMock(return_value=["node1", "node2", "node3"])
    return mock_graph


@pytest.fixture
def mock_aiocache(mocker):
    """
    Mock aiocache for cache testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock aiocache instance
    """
    mock_cache = mocker.MagicMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=True)
    return mock_cache


@pytest.fixture
def mock_stamina_retry(mocker):
    """
    Mock stamina retry decorator for testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock stamina retry
    """
    def mock_retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    mocker.patch("stamina.retry", side_effect=mock_retry)
    return mock_retry


@pytest.fixture
def mock_structlog(mocker):
    """
    Mock structlog for logging testing.
    
    Args:
        mocker: pytest-mock mocker fixture
        
    Returns:
        Mock structlog logger
    """
    mock_logger = mocker.MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.exception = MagicMock()
    
    mocker.patch("structlog.get_logger", return_value=mock_logger)
    return mock_logger


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """
    Get performance test data.
    
    Returns:
        Dictionary with performance test data
    """
    return {
        "small_text": "This is a short text for performance testing.",
        "medium_text": "This is a medium length text for performance testing. " * 10,
        "large_text": "This is a large text for performance testing. " * 100,
        "expected_max_latency": 5000  # 5 seconds
    }


# Integration testing fixtures
@pytest.fixture
def integration_test_settings() -> Settings:
    """
    Create settings for integration testing.
    
    Returns:
        Settings configured for integration tests
    """
    return Settings(
        api_keys_allowed="integration_test_key",
        llm_provider="gemini",
        gemini_api_key=os.getenv("TEST_GEMINI_API_KEY", "test_key"),
        gemini_model="gemini-pro",
        summary_max_tokens=100,
        lang_default="auto",
        request_timeout_ms=30000,  # Longer timeout for integration tests
        enable_rate_limit=True,
        redis_url=os.getenv("TEST_REDIS_URL", "redis://localhost:6379/2"),
        cors_origins=["*"],
        log_level="INFO",
        enable_auto_evaluation=True,
        evaluation_model="all-MiniLM-L6-v2",
        cache_ttl_seconds=3600,
        api_title="Integration Test LLM API",
        api_version="1.0.0-integration"
    )


# Export fixtures
__all__ = [
    "event_loop",
    "test_settings",
    "app",
    "client",
    "async_client",
    "mock_gemini_provider",
    "mock_fallback_provider",
    "mock_cache_service",
    "mock_evaluation_service",
    "valid_api_key",
    "invalid_api_key",
    "auth_headers",
    "invalid_auth_headers",
    "temp_dir",
    "mock_redis",
    "mock_httpx_client",
    "mock_sentence_transformer",
    "mock_rouge_scorer",
    "mock_sumy_summarizer",
    "mock_networkx_graph",
    "mock_aiocache",
    "mock_stamina_retry",
    "mock_structlog",
    "performance_test_data",
    "integration_test_settings",
]
