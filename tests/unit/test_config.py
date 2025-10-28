"""
Unit tests for configuration module.

Tests Settings validation, environment variable loading,
and configuration defaults.
"""

import os
import pytest
from pydantic import ValidationError

from app.config import Settings, get_cached_settings
from tests.fixtures.test_data import TEST_REQUESTS


class TestSettings:
    """Test Settings class functionality."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        assert settings.api_title == "LLM Summarization API"
        assert settings.api_version == "1.0.0"
        assert settings.log_level == "INFO"
        assert settings.enable_rate_limit is True
        assert settings.enable_auto_evaluation is True
        assert settings.cache_ttl_seconds == 3600
    
    def test_custom_settings(self):
        """Test custom settings values."""
        settings = Settings(
            api_title="Custom API",
            api_version="2.0.0",
            log_level="DEBUG",
            enable_rate_limit=False,
            enable_auto_evaluation=False,
            cache_ttl_seconds=7200
        )
        
        assert settings.api_title == "Custom API"
        assert settings.api_version == "2.0.0"
        assert settings.log_level == "DEBUG"
        assert settings.enable_rate_limit is False
        assert settings.enable_auto_evaluation is False
        assert settings.cache_ttl_seconds == 7200
    
    def test_api_keys_validation(self):
        """Test API keys validation."""
        # Valid API keys
        settings = Settings(api_keys_allowed="key1,key2,key3")
        assert len(settings.api_keys_allowed) == 3
        assert "key1" in settings.api_keys_allowed
        assert "key2" in settings.api_keys_allowed
        assert "key3" in settings.api_keys_allowed
        
        # Empty API keys should raise error
        with pytest.raises(ValidationError):
            Settings(api_keys_allowed="")
    
    def test_gemini_api_key_validation(self):
        """Test Gemini API key validation."""
        # Valid API key
        settings = Settings(gemini_api_key="valid_key_123")
        assert settings.gemini_api_key == "valid_key_123"
        
        # Empty API key should raise error
        with pytest.raises(ValidationError):
            Settings(gemini_api_key="")
    
    def test_summary_max_tokens_validation(self):
        """Test summary max tokens validation."""
        # Valid range
        settings = Settings(summary_max_tokens=100)
        assert settings.summary_max_tokens == 100
        
        # Too low
        with pytest.raises(ValidationError):
            Settings(summary_max_tokens=5)
        
        # Too high
        with pytest.raises(ValidationError):
            Settings(summary_max_tokens=1000)
    
    def test_request_timeout_validation(self):
        """Test request timeout validation."""
        # Valid timeout
        settings = Settings(request_timeout_ms=10000)
        assert settings.request_timeout_ms == 10000
        
        # Too low
        with pytest.raises(ValidationError):
            Settings(request_timeout_ms=100)
        
        # Too high
        with pytest.raises(ValidationError):
            Settings(request_timeout_ms=300000)
    
    def test_redis_url_validation(self):
        """Test Redis URL validation."""
        # Valid Redis URL
        settings = Settings(redis_url="redis://localhost:6379/0")
        assert settings.redis_url == "redis://localhost:6379/0"
        
        # Invalid URL format
        with pytest.raises(ValidationError):
            Settings(redis_url="invalid_url")
    
    def test_cors_origins_validation(self):
        """Test CORS origins validation."""
        # Single origin
        settings = Settings(cors_origins=["https://example.com"])
        assert settings.cors_origins == ["https://example.com"]
        
        # Multiple origins
        settings = Settings(cors_origins=["https://example.com", "https://test.com"])
        assert len(settings.cors_origins) == 2
        
        # Wildcard
        settings = Settings(cors_origins=["*"])
        assert settings.cors_origins == ["*"]
    
    def test_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level
        
        # Invalid level
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
    
    def test_cache_ttl_validation(self):
        """Test cache TTL validation."""
        # Valid TTL
        settings = Settings(cache_ttl_seconds=3600)
        assert settings.cache_ttl_seconds == 3600
        
        # Too low
        with pytest.raises(ValidationError):
            Settings(cache_ttl_seconds=0)
        
        # Too high
        with pytest.raises(ValidationError):
            Settings(cache_ttl_seconds=86400 * 7)  # 7 days
    
    def test_evaluation_model_validation(self):
        """Test evaluation model validation."""
        # Valid model
        settings = Settings(evaluation_model="all-MiniLM-L6-v2")
        assert settings.evaluation_model == "all-MiniLM-L6-v2"
        
        # Empty model should raise error
        with pytest.raises(ValidationError):
            Settings(evaluation_model="")


class TestSettingsComputedProperties:
    """Test computed properties of Settings."""
    
    def test_api_keys_set(self):
        """Test api_keys_allowed computed property."""
        settings = Settings(api_keys_allowed="key1,key2,key3")
        assert settings.api_keys_allowed == {"key1", "key2", "key3"}
    
    def test_cors_origins_list(self):
        """Test cors_origins computed property."""
        settings = Settings(cors_origins=["https://example.com", "https://test.com"])
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) == 2


class TestGetCachedSettings:
    """Test get_cached_settings function."""
    
    def test_cached_settings_singleton(self):
        """Test that get_cached_settings returns singleton."""
        settings1 = get_cached_settings()
        settings2 = get_cached_settings()
        
        assert settings1 is settings2
    
    def test_cached_settings_immutable(self):
        """Test that cached settings are immutable."""
        settings = get_cached_settings()
        
        # Should not be able to modify cached settings
        with pytest.raises(AttributeError):
            settings.api_title = "Modified"
    
    def test_cached_settings_environment_override(self):
        """Test that environment variables override cached settings."""
        # Set environment variable
        os.environ["API_TITLE"] = "Environment Override"
        
        try:
            # Clear cache to force reload
            import app.config
            app.config._cached_settings = None
            
            settings = get_cached_settings()
            assert settings.api_title == "Environment Override"
        
        finally:
            # Clean up
            del os.environ["API_TITLE"]
            app.config._cached_settings = None


class TestSettingsEnvironmentVariables:
    """Test Settings with environment variables."""
    
    def test_environment_variable_loading(self):
        """Test loading settings from environment variables."""
        # Set environment variables
        env_vars = {
            "API_KEYS_ALLOWED": "env_key1,env_key2",
            "GEMINI_API_KEY": "env_gemini_key",
            "SUMMARY_MAX_TOKENS": "200",
            "LOG_LEVEL": "DEBUG",
            "ENABLE_RATE_LIMIT": "false",
            "REDIS_URL": "redis://localhost:6379/1"
        }
        
        # Store original values
        original_values = {}
        for key, value in env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            # Create settings (should load from environment)
            settings = Settings()
            
            assert "env_key1" in settings.api_keys_allowed
            assert "env_key2" in settings.api_keys_allowed
            assert settings.gemini_api_key == "env_gemini_key"
            assert settings.summary_max_tokens == 200
            assert settings.log_level == "DEBUG"
            assert settings.enable_rate_limit is False
            assert settings.redis_url == "redis://localhost:6379/1"
        
        finally:
            # Restore original values
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
    
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        # Test true values
        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]
        
        for value in true_values:
            os.environ["ENABLE_RATE_LIMIT"] = value
            try:
                settings = Settings()
                assert settings.enable_rate_limit is True
            finally:
                del os.environ["ENABLE_RATE_LIMIT"]
        
        # Test false values
        false_values = ["false", "False", "FALSE", "0", "no", "No", "NO"]
        
        for value in false_values:
            os.environ["ENABLE_RATE_LIMIT"] = value
            try:
                settings = Settings()
                assert settings.enable_rate_limit is False
            finally:
                del os.environ["ENABLE_RATE_LIMIT"]
    
    def test_integer_environment_variables(self):
        """Test integer environment variable parsing."""
        os.environ["SUMMARY_MAX_TOKENS"] = "150"
        try:
            settings = Settings()
            assert settings.summary_max_tokens == 150
        finally:
            del os.environ["SUMMARY_MAX_TOKENS"]
        
        # Test invalid integer
        os.environ["SUMMARY_MAX_TOKENS"] = "invalid"
        try:
            with pytest.raises(ValidationError):
                Settings()
        finally:
            del os.environ["SUMMARY_MAX_TOKENS"]


class TestSettingsEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_string_values(self):
        """Test handling of empty string values."""
        with pytest.raises(ValidationError):
            Settings(
                api_keys_allowed="",
                gemini_api_key="",
                evaluation_model=""
            )
    
    def test_none_values(self):
        """Test handling of None values."""
        with pytest.raises(ValidationError):
            Settings(
                api_keys_allowed=None,
                gemini_api_key=None
            )
    
    def test_whitespace_values(self):
        """Test handling of whitespace-only values."""
        with pytest.raises(ValidationError):
            Settings(
                api_keys_allowed="   ",
                gemini_api_key="   "
            )
    
    def test_special_characters_in_api_keys(self):
        """Test handling of special characters in API keys."""
        # Should work with special characters
        settings = Settings(api_keys_allowed="key-with-dash,key_with_underscore,key.with.dots")
        assert len(settings.api_keys_allowed) == 3
    
    def test_very_long_values(self):
        """Test handling of very long values."""
        long_key = "a" * 1000
        settings = Settings(api_keys_allowed=long_key)
        assert long_key in settings.api_keys_allowed


# Export test classes
__all__ = [
    "TestSettings",
    "TestSettingsComputedProperties", 
    "TestGetCachedSettings",
    "TestSettingsEnvironmentVariables",
    "TestSettingsEdgeCases",
]
