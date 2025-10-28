"""
LLM Summarization Microservice.

A production-ready FastAPI microservice for text summarization using
Google Gemini with automatic fallback to extractive summarization.

Features:
- Google Gemini LLM integration with retries
- TextRank extractive fallback
- Redis caching and rate limiting
- Automatic quality evaluation
- Structured JSON logging
- Docker containerization
"""

__version__ = "1.0.0"
__author__ = "LLM Summarization Team"
