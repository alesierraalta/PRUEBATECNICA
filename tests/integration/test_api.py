"""
Integration tests for API endpoints.

Tests complete API functionality including authentication,
rate limiting, error handling, and end-to-end workflows.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import create_app
from tests.fixtures.test_data import (
    TEST_REQUESTS,
    INVALID_REQUESTS,
    MOCK_GEMINI_RESPONSE,
    MOCK_FALLBACK_RESPONSE,
    MOCK_EVALUATION_METRICS,
    ERROR_SCENARIOS
)


class TestSummarizeEndpoint:
    """Test POST /v1/summarize endpoint."""
    
    def test_successful_summarization(self, client: TestClient, auth_headers: dict):
        """Test successful text summarization."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "summary" in data
            assert "usage" in data
            assert "model" in data
            assert "latency_ms" in data
            assert data["cached"] is False
            
            # Verify provider was called
            mock_provider.summarize.assert_called_once()
    
    def test_summarization_with_cache(self, client: TestClient, auth_headers: dict):
        """Test summarization with cached result."""
        with patch("app.api.v1.summarize.get_cache_service") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_cache.return_value = mock_cache
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["cached"] is True
            assert data["latency_ms"] < 100  # Should be very fast from cache
    
    def test_summarization_with_fallback(self, client: TestClient, auth_headers: dict):
        """Test summarization with LLM fallback."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_llm, \
             patch("app.api.v1.summarize.get_fallback_provider") as mock_get_fallback:
            
            # LLM provider fails
            mock_llm = AsyncMock()
            mock_llm.summarize = AsyncMock(side_effect=Exception("LLM Error"))
            mock_get_llm.return_value = mock_llm
            
            # Fallback provider succeeds
            mock_fallback = AsyncMock()
            mock_fallback.summarize = AsyncMock(return_value=MOCK_FALLBACK_RESPONSE)
            mock_get_fallback.return_value = mock_fallback
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["model"] == "textrank-extractive"
            assert "summary" in data
    
    def test_summarization_with_evaluation(self, client: TestClient, auth_headers: dict):
        """Test summarization with quality evaluation."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider, \
             patch("app.api.v1.summarize.get_evaluator") as mock_get_evaluator:
            
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            mock_evaluator = AsyncMock()
            mock_evaluator.evaluate = AsyncMock(return_value=MOCK_EVALUATION_METRICS)
            mock_get_evaluator.return_value = mock_evaluator
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "evaluation" in data
            assert data["evaluation"]["quality_score"] == 0.78
    
    def test_validation_error_empty_text(self, client: TestClient, auth_headers: dict):
        """Test validation error for empty text."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["empty_text"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_validation_error_text_too_short(self, client: TestClient, auth_headers: dict):
        """Test validation error for text too short."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["text_too_short"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_validation_error_invalid_language(self, client: TestClient, auth_headers: dict):
        """Test validation error for invalid language."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["invalid_language"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_validation_error_invalid_tone(self, client: TestClient, auth_headers: dict):
        """Test validation error for invalid tone."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["invalid_tone"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_validation_error_max_tokens_too_low(self, client: TestClient, auth_headers: dict):
        """Test validation error for max tokens too low."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["max_tokens_too_low"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_validation_error_max_tokens_too_high(self, client: TestClient, auth_headers: dict):
        """Test validation error for max tokens too high."""
        response = client.post(
            "/v1/summarize",
            json=INVALID_REQUESTS["max_tokens_too_high"],
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "validation_error" in data["error"]
    
    def test_authentication_required(self, client: TestClient):
        """Test that authentication is required."""
        response = client.post(
            "/v1/summarize",
            json=TEST_REQUESTS["valid"]
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "authentication_error" in data["error"]
    
    def test_invalid_api_key(self, client: TestClient, invalid_auth_headers: dict):
        """Test invalid API key."""
        response = client.post(
            "/v1/summarize",
            json=TEST_REQUESTS["valid"],
            headers=invalid_auth_headers
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "authentication_error" in data["error"]
    
    def test_malformed_auth_header(self, client: TestClient):
        """Test malformed authorization header."""
        response = client.post(
            "/v1/summarize",
            json=TEST_REQUESTS["valid"],
            headers={"Authorization": "InvalidFormat"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "authentication_error" in data["error"]
    
    def test_missing_auth_header(self, client: TestClient):
        """Test missing authorization header."""
        response = client.post(
            "/v1/summarize",
            json=TEST_REQUESTS["valid"],
            headers={}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "authentication_error" in data["error"]
    
    def test_service_unavailable_error(self, client: TestClient, auth_headers: dict):
        """Test service unavailable error."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_llm, \
             patch("app.api.v1.summarize.get_fallback_provider") as mock_get_fallback:
            
            # Both providers fail
            mock_llm = AsyncMock()
            mock_llm.summarize = AsyncMock(side_effect=Exception("LLM Error"))
            mock_get_llm.return_value = mock_llm
            
            mock_fallback = AsyncMock()
            mock_fallback.summarize = AsyncMock(side_effect=Exception("Fallback Error"))
            mock_get_fallback.return_value = mock_fallback
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert "service_unavailable" in data["error"]
    
    def test_multilingual_support(self, client: TestClient, auth_headers: dict):
        """Test multilingual text support."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["multilingual"],
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
    
    def test_different_tones(self, client: TestClient, auth_headers: dict):
        """Test different summary tones."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            tones = ["neutral", "concise", "bullet"]
            
            for tone in tones:
                request_data = TEST_REQUESTS["valid"].copy()
                request_data["tone"] = tone
                
                response = client.post(
                    "/v1/summarize",
                    json=request_data,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "summary" in data
    
    def test_different_token_limits(self, client: TestClient, auth_headers: dict):
        """Test different token limits."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            token_limits = [50, 100, 200, 300]
            
            for limit in token_limits:
                request_data = TEST_REQUESTS["valid"].copy()
                request_data["max_tokens"] = limit
                
                response = client.post(
                    "/v1/summarize",
                    json=request_data,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "summary" in data


class TestHealthEndpoint:
    """Test GET /v1/healthz endpoint."""
    
    def test_healthy_health_check(self, client: TestClient):
        """Test healthy health check."""
        with patch("app.api.v1.health.check_llm_provider") as mock_check_llm, \
             patch("app.api.v1.health.check_cache_service") as mock_check_cache:
            
            # Mock healthy services
            mock_check_llm.return_value = AsyncMock(
                status="healthy",
                response_time_ms=150,
                details={"model": "gemini-pro"}
            )
            
            mock_check_cache.return_value = AsyncMock(
                status="healthy",
                response_time_ms=5,
                details={"connected_clients": 10}
            )
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "services" in data
            assert "timestamp" in data
            assert "version" in data
    
    def test_degraded_health_check(self, client: TestClient):
        """Test degraded health check."""
        with patch("app.api.v1.health.check_llm_provider") as mock_check_llm, \
             patch("app.api.v1.health.check_cache_service") as mock_check_cache:
            
            # Mock degraded services
            mock_check_llm.return_value = AsyncMock(
                status="healthy",
                response_time_ms=150
            )
            
            mock_check_cache.return_value = AsyncMock(
                status="unhealthy",
                response_time_ms=5000,
                error="Connection timeout"
            )
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["services"]["redis"]["status"] == "unhealthy"
    
    def test_unhealthy_health_check(self, client: TestClient):
        """Test unhealthy health check."""
        with patch("app.api.v1.health.check_llm_provider") as mock_check_llm, \
             patch("app.api.v1.health.check_cache_service") as mock_check_cache:
            
            # Mock unhealthy services
            mock_check_llm.return_value = AsyncMock(
                status="unhealthy",
                response_time_ms=10000,
                error="API key invalid"
            )
            
            mock_check_cache.return_value = AsyncMock(
                status="unhealthy",
                response_time_ms=5000,
                error="Connection refused"
            )
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == 503
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["services"]["llm_provider"]["status"] == "unhealthy"
    
    def test_health_check_with_evaluation_service(self, client: TestClient):
        """Test health check with evaluation service."""
        with patch("app.api.v1.health.check_llm_provider") as mock_check_llm, \
             patch("app.api.v1.health.check_cache_service") as mock_check_cache, \
             patch("app.api.v1.health.check_evaluation_service") as mock_check_eval:
            
            # Mock all services
            mock_check_llm.return_value = AsyncMock(status="healthy")
            mock_check_cache.return_value = AsyncMock(status="healthy")
            mock_check_eval.return_value = AsyncMock(status="healthy")
            
            response = client.get("/v1/healthz")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "evaluation_service" in data["services"]
    
    def test_health_check_no_auth_required(self, client: TestClient):
        """Test that health check doesn't require authentication."""
        response = client.get("/v1/healthz")
        
        # Should not return 401 even without auth headers
        assert response.status_code in [200, 503]  # Either healthy or unhealthy


class TestRootEndpoints:
    """Test root endpoints."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "timestamp" in data
        assert "docs_url" in data
        assert "health_url" in data
    
    def test_simple_health_endpoint(self, client: TestClient):
        """Test simple health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_404_not_found(self, client: TestClient):
        """Test 404 for non-existent endpoints."""
        response = client.get("/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 for unsupported HTTP methods."""
        response = client.put("/v1/summarize")
        
        assert response.status_code == 405
    
    def test_422_unprocessable_entity(self, client: TestClient, auth_headers: dict):
        """Test 422 for malformed JSON."""
        response = client.post(
            "/v1/summarize",
            json={"invalid": "data"},
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    def test_500_internal_server_error(self, client: TestClient, auth_headers: dict):
        """Test 500 for unexpected errors."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            # Mock unexpected error
            mock_get_provider.side_effect = Exception("Unexpected error")
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "internal_server_error" in data["error"]


class TestPerformance:
    """Test performance characteristics."""
    
    def test_response_time_reasonable(self, client: TestClient, auth_headers: dict):
        """Test that response times are reasonable."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            import time
            start_time = time.time()
            
            response = client.post(
                "/v1/summarize",
                json=TEST_REQUESTS["valid"],
                headers=auth_headers
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            assert response.status_code == 200
            assert response_time < 5000  # Should respond within 5 seconds
    
    def test_concurrent_requests(self, client: TestClient, auth_headers: dict):
        """Test handling of concurrent requests."""
        with patch("app.api.v1.summarize.get_llm_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.summarize = AsyncMock(return_value=MOCK_GEMINI_RESPONSE)
            mock_get_provider.return_value = mock_provider
            
            import threading
            import time
            
            responses = []
            errors = []
            
            def make_request():
                try:
                    response = client.post(
                        "/v1/summarize",
                        json=TEST_REQUESTS["valid"],
                        headers=auth_headers
                    )
                    responses.append(response)
                except Exception as e:
                    errors.append(e)
            
            # Start multiple concurrent requests
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All requests should succeed
            assert len(responses) == 5
            assert len(errors) == 0
            
            for response in responses:
                assert response.status_code == 200


# Export test classes
__all__ = [
    "TestSummarizeEndpoint",
    "TestHealthEndpoint",
    "TestRootEndpoints",
    "TestErrorHandling",
    "TestPerformance",
]
