"""
Unit tests for API schemas.

Tests Pydantic schema validation, error handling,
and data transformation for all API models.
"""

import pytest
from pydantic import ValidationError

from app.api.schemas.summarize import (
    SummarizeRequest,
    SummarizeResponse,
    TokenUsage,
    EvaluationMetrics
)
from app.api.schemas.health import (
    ServiceStatus,
    HealthResponse
)
from tests.fixtures.test_data import (
    TEST_REQUESTS,
    INVALID_REQUESTS,
    MOCK_GEMINI_RESPONSE,
    MOCK_EVALUATION_METRICS,
    MOCK_HEALTH_RESPONSES
)


class TestSummarizeRequest:
    """Test SummarizeRequest schema validation."""
    
    def test_valid_request(self):
        """Test valid request data."""
        request = SummarizeRequest(**TEST_REQUESTS["valid"])
        
        assert request.text == TEST_REQUESTS["valid"]["text"]
        assert request.lang == "en"
        assert request.max_tokens == 100
        assert request.tone == "neutral"
    
    def test_minimal_request(self):
        """Test minimal request data."""
        request = SummarizeRequest(**TEST_REQUESTS["minimal"])
        
        assert request.text == TEST_REQUESTS["minimal"]["text"]
        assert request.lang == "auto"
        assert request.max_tokens == 50
        assert request.tone == "concise"
    
    def test_maximal_request(self):
        """Test maximal request data."""
        request = SummarizeRequest(**TEST_REQUESTS["maximal"])
        
        assert request.text == TEST_REQUESTS["maximal"]["text"]
        assert request.lang == "en"
        assert request.max_tokens == 500
        assert request.tone == "bullet"
    
    def test_multilingual_request(self):
        """Test multilingual request data."""
        request = SummarizeRequest(**TEST_REQUESTS["multilingual"])
        
        assert request.text == TEST_REQUESTS["multilingual"]["text"]
        assert request.lang == "es"
        assert request.max_tokens == 100
        assert request.tone == "neutral"
    
    def test_empty_text_validation(self):
        """Test empty text validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["empty_text"])
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)
    
    def test_text_too_short_validation(self):
        """Test text too short validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["text_too_short"])
        
        errors = exc_info.value.errors()
        assert any("too short" in str(error["msg"]).lower() for error in errors)
    
    def test_text_too_long_validation(self):
        """Test text too long validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["text_too_long"])
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)
    
    def test_invalid_language_validation(self):
        """Test invalid language validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["invalid_language"])
        
        errors = exc_info.value.errors()
        assert any("unsupported language" in str(error["msg"]).lower() for error in errors)
    
    def test_invalid_tone_validation(self):
        """Test invalid tone validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["invalid_tone"])
        
        errors = exc_info.value.errors()
        assert any("unsupported tone" in str(error["msg"]).lower() for error in errors)
    
    def test_max_tokens_too_low_validation(self):
        """Test max tokens too low validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["max_tokens_too_low"])
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)
    
    def test_max_tokens_too_high_validation(self):
        """Test max tokens too high validation."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(**INVALID_REQUESTS["max_tokens_too_high"])
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)
    
    def test_text_stripping(self):
        """Test that text is stripped of whitespace."""
        request = SummarizeRequest(
            text="  This is a test text.  ",
            lang="en",
            max_tokens=100,
            tone="neutral"
        )
        
        assert request.text == "This is a test text."
    
    def test_word_count_validation(self):
        """Test word count validation."""
        # Text with insufficient words
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(
                text="Hi there",
                lang="en",
                max_tokens=100,
                tone="neutral"
            )
        
        errors = exc_info.value.errors()
        assert any("minimum 5 words" in str(error["msg"]).lower() for error in errors)
    
    def test_meaningful_content_validation(self):
        """Test meaningful content validation."""
        # Text with repeated characters
        with pytest.raises(ValidationError) as exc_info:
            SummarizeRequest(
                text="aaa bbb ccc",
                lang="en",
                max_tokens=100,
                tone="neutral"
            )
        
        errors = exc_info.value.errors()
        assert any("insufficient meaningful content" in str(error["msg"]).lower() for error in errors)


class TestTokenUsage:
    """Test TokenUsage schema validation."""
    
    def test_valid_token_usage(self):
        """Test valid token usage data."""
        usage = TokenUsage(
            prompt_tokens=120,
            completion_tokens=40,
            total_tokens=160
        )
        
        assert usage.prompt_tokens == 120
        assert usage.completion_tokens == 40
        assert usage.total_tokens == 160
    
    def test_zero_tokens(self):
        """Test zero token values."""
        usage = TokenUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
    
    def test_negative_tokens_validation(self):
        """Test negative token validation."""
        with pytest.raises(ValidationError):
            TokenUsage(
                prompt_tokens=-1,
                completion_tokens=40,
                total_tokens=160
            )
    
    def test_missing_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=120)


class TestEvaluationMetrics:
    """Test EvaluationMetrics schema validation."""
    
    def test_valid_evaluation_metrics(self):
        """Test valid evaluation metrics."""
        metrics = EvaluationMetrics(**MOCK_EVALUATION_METRICS)
        
        assert metrics.rouge_1_f == 0.75
        assert metrics.rouge_2_f == 0.65
        assert metrics.rouge_l_f == 0.70
        assert metrics.semantic_similarity == 0.85
        assert metrics.compression_ratio == 0.20
        assert metrics.quality_score == 0.78
    
    def test_perfect_scores(self):
        """Test perfect evaluation scores."""
        metrics = EvaluationMetrics(
            rouge_1_f=1.0,
            rouge_2_f=1.0,
            rouge_l_f=1.0,
            semantic_similarity=1.0,
            compression_ratio=1.0,
            quality_score=1.0
        )
        
        assert all(score == 1.0 for score in [
            metrics.rouge_1_f,
            metrics.rouge_2_f,
            metrics.rouge_l_f,
            metrics.semantic_similarity,
            metrics.compression_ratio,
            metrics.quality_score
        ])
    
    def test_zero_scores(self):
        """Test zero evaluation scores."""
        metrics = EvaluationMetrics(
            rouge_1_f=0.0,
            rouge_2_f=0.0,
            rouge_l_f=0.0,
            semantic_similarity=0.0,
            compression_ratio=0.0,
            quality_score=0.0
        )
        
        assert all(score == 0.0 for score in [
            metrics.rouge_1_f,
            metrics.rouge_2_f,
            metrics.rouge_l_f,
            metrics.semantic_similarity,
            metrics.compression_ratio,
            metrics.quality_score
        ])
    
    def test_out_of_range_scores_validation(self):
        """Test out of range scores validation."""
        with pytest.raises(ValidationError):
            EvaluationMetrics(
                rouge_1_f=1.5,  # > 1.0
                rouge_2_f=0.65,
                rouge_l_f=0.70,
                semantic_similarity=0.85,
                compression_ratio=0.20,
                quality_score=0.78
            )
    
    def test_negative_scores_validation(self):
        """Test negative scores validation."""
        with pytest.raises(ValidationError):
            EvaluationMetrics(
                rouge_1_f=-0.1,  # < 0.0
                rouge_2_f=0.65,
                rouge_l_f=0.70,
                semantic_similarity=0.85,
                compression_ratio=0.20,
                quality_score=0.78
            )


class TestSummarizeResponse:
    """Test SummarizeResponse schema validation."""
    
    def test_valid_response(self):
        """Test valid response data."""
        response = SummarizeResponse(**MOCK_GEMINI_RESPONSE)
        
        assert response.summary == MOCK_GEMINI_RESPONSE["summary"]
        assert response.usage.prompt_tokens == 120
        assert response.usage.completion_tokens == 40
        assert response.usage.total_tokens == 160
        assert response.model == "gemini-pro"
        assert response.latency_ms == 1250
        assert response.cached is False
    
    def test_response_with_evaluation(self):
        """Test response with evaluation metrics."""
        response_data = MOCK_GEMINI_RESPONSE.copy()
        response_data["evaluation"] = MOCK_EVALUATION_METRICS
        
        response = SummarizeResponse(**response_data)
        
        assert response.evaluation is not None
        assert response.evaluation.quality_score == 0.78
    
    def test_response_without_evaluation(self):
        """Test response without evaluation metrics."""
        response = SummarizeResponse(**MOCK_GEMINI_RESPONSE)
        
        assert response.evaluation is None
    
    def test_cached_response(self):
        """Test cached response."""
        response_data = MOCK_GEMINI_RESPONSE.copy()
        response_data["cached"] = True
        
        response = SummarizeResponse(**response_data)
        
        assert response.cached is True
    
    def test_negative_latency_validation(self):
        """Test negative latency validation."""
        response_data = MOCK_GEMINI_RESPONSE.copy()
        response_data["latency_ms"] = -1
        
        with pytest.raises(ValidationError):
            SummarizeResponse(**response_data)
    
    def test_missing_required_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            SummarizeResponse(summary="Test summary")


class TestServiceStatus:
    """Test ServiceStatus schema validation."""
    
    def test_healthy_service_status(self):
        """Test healthy service status."""
        status = ServiceStatus(
            status="healthy",
            response_time_ms=150,
            details={"model": "gemini-pro"}
        )
        
        assert status.status == "healthy"
        assert status.response_time_ms == 150
        assert status.error is None
        assert status.details["model"] == "gemini-pro"
    
    def test_unhealthy_service_status(self):
        """Test unhealthy service status."""
        status = ServiceStatus(
            status="unhealthy",
            response_time_ms=5000,
            error="Connection timeout",
            details={"provider": "gemini"}
        )
        
        assert status.status == "unhealthy"
        assert status.response_time_ms == 5000
        assert status.error == "Connection timeout"
        assert status.details["provider"] == "gemini"
    
    def test_degraded_service_status(self):
        """Test degraded service status."""
        status = ServiceStatus(
            status="degraded",
            response_time_ms=2000,
            details={"version": "1.0.0"}
        )
        
        assert status.status == "degraded"
        assert status.response_time_ms == 2000
        assert status.error is None
        assert status.details["version"] == "1.0.0"
    
    def test_negative_response_time_validation(self):
        """Test negative response time validation."""
        with pytest.raises(ValidationError):
            ServiceStatus(
                status="healthy",
                response_time_ms=-1
            )
    
    def test_missing_status(self):
        """Test missing required status field."""
        with pytest.raises(ValidationError):
            ServiceStatus(response_time_ms=150)


class TestHealthResponse:
    """Test HealthResponse schema validation."""
    
    def test_healthy_health_response(self):
        """Test healthy health response."""
        response = HealthResponse(**MOCK_HEALTH_RESPONSES["healthy"])
        
        assert response.status == "healthy"
        assert response.timestamp == 1640995200.123
        assert len(response.services) == 2
        assert response.services["llm_provider"].status == "healthy"
        assert response.services["redis"].status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 86400.0
    
    def test_degraded_health_response(self):
        """Test degraded health response."""
        response = HealthResponse(**MOCK_HEALTH_RESPONSES["degraded"])
        
        assert response.status == "degraded"
        assert response.services["llm_provider"].status == "healthy"
        assert response.services["redis"].status == "unhealthy"
    
    def test_unhealthy_health_response(self):
        """Test unhealthy health response."""
        response = HealthResponse(**MOCK_HEALTH_RESPONSES["unhealthy"])
        
        assert response.status == "unhealthy"
        assert response.services["llm_provider"].status == "unhealthy"
        assert response.services["redis"].status == "unhealthy"
    
    def test_health_response_without_uptime(self):
        """Test health response without uptime."""
        response_data = MOCK_HEALTH_RESPONSES["healthy"].copy()
        del response_data["uptime_seconds"]
        
        response = HealthResponse(**response_data)
        
        assert response.uptime_seconds is None
    
    def test_negative_timestamp_validation(self):
        """Test negative timestamp validation."""
        response_data = MOCK_HEALTH_RESPONSES["healthy"].copy()
        response_data["timestamp"] = -1
        
        with pytest.raises(ValidationError):
            HealthResponse(**response_data)
    
    def test_missing_required_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            HealthResponse(status="healthy")


class TestSchemaSerialization:
    """Test schema serialization and deserialization."""
    
    def test_summarize_request_serialization(self):
        """Test SummarizeRequest serialization."""
        request = SummarizeRequest(**TEST_REQUESTS["valid"])
        
        # Test dict conversion
        request_dict = request.dict()
        assert request_dict["text"] == TEST_REQUESTS["valid"]["text"]
        assert request_dict["lang"] == "en"
        assert request_dict["max_tokens"] == 100
        assert request_dict["tone"] == "neutral"
        
        # Test JSON conversion
        request_json = request.json()
        assert isinstance(request_json, str)
        assert "text" in request_json
    
    def test_summarize_response_serialization(self):
        """Test SummarizeResponse serialization."""
        response = SummarizeResponse(**MOCK_GEMINI_RESPONSE)
        
        # Test dict conversion
        response_dict = response.dict()
        assert response_dict["summary"] == MOCK_GEMINI_RESPONSE["summary"]
        assert response_dict["model"] == "gemini-pro"
        assert response_dict["cached"] is False
        
        # Test JSON conversion
        response_json = response.json()
        assert isinstance(response_json, str)
        assert "summary" in response_json
    
    def test_health_response_serialization(self):
        """Test HealthResponse serialization."""
        response = HealthResponse(**MOCK_HEALTH_RESPONSES["healthy"])
        
        # Test dict conversion
        response_dict = response.dict()
        assert response_dict["status"] == "healthy"
        assert response_dict["version"] == "1.0.0"
        assert len(response_dict["services"]) == 2
        
        # Test JSON conversion
        response_json = response.json()
        assert isinstance(response_json, str)
        assert "status" in response_json


# Export test classes
__all__ = [
    "TestSummarizeRequest",
    "TestTokenUsage",
    "TestEvaluationMetrics",
    "TestSummarizeResponse",
    "TestServiceStatus",
    "TestHealthResponse",
    "TestSchemaSerialization",
]
