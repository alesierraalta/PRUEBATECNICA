"""
Automatic summary quality evaluator.

Provides comprehensive evaluation of summary quality using multiple metrics:
- ROUGE scores (lexical overlap)
- Semantic similarity (embedding-based)
- Compression ratio analysis
- Composite quality score

Uses lazy loading for ML models to optimize memory usage and startup time.
"""

import time
from functools import lru_cache
from typing import TypedDict, Final

import numpy as np
import rouge_score
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.constants import (
    EVALUATION_MODEL_DEFAULT,
    ROUGE_METRICS,
    IDEAL_COMPRESSION_RATIO,
    COMPRESSION_TOLERANCE,
)


class EvaluationMetrics(TypedDict):
    """
    Comprehensive evaluation metrics for summary quality.
    
    Provides detailed metrics for assessing summary quality across
    multiple dimensions including lexical overlap, semantic similarity,
    and compression appropriateness.
    
    Attributes:
        rouge_1_f: ROUGE-1 F-score (unigram overlap)
        rouge_2_f: ROUGE-2 F-score (bigram overlap)
        rouge_l_f: ROUGE-L F-score (longest common subsequence)
        semantic_similarity: Cosine similarity between embeddings
        compression_ratio: Ratio of summary length to original length
        quality_score: Weighted composite quality score (0-1)
    """
    rouge_1_f: float
    rouge_2_f: float
    rouge_l_f: float
    semantic_similarity: float
    compression_ratio: float
    quality_score: float


class SummaryEvaluator:
    """
    Automatic summary quality evaluator with comprehensive metrics.
    
    Evaluates summaries using multiple complementary metrics to provide
    a holistic assessment of quality. Combines lexical overlap (ROUGE),
    semantic similarity (embeddings), and compression analysis.
    
    Features:
    - ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L) for lexical overlap
    - Semantic similarity using sentence transformers
    - Compression ratio analysis with ideal range validation
    - Composite quality score with weighted combination
    - Lazy loading of ML models for memory efficiency
    - Robust error handling with graceful degradation
    
    Attributes:
        model_name: Sentence transformer model for semantic similarity
        rouge_scorer: ROUGE scorer instance for lexical metrics
    """
    
    # Quality score weights
    ROUGE_L_WEIGHT: Final[float] = 0.30
    SEMANTIC_WEIGHT: Final[float] = 0.40
    COMPRESSION_WEIGHT: Final[float] = 0.30
    
    def __init__(self, model_name: str = EVALUATION_MODEL_DEFAULT):
        """
        Initialize summary evaluator.
        
        Sets up the evaluator with ROUGE scorer and prepares for
        lazy loading of the semantic similarity model.
        
        Args:
            model_name: Sentence transformer model name for embeddings
            
        Example:
            ```python
            evaluator = SummaryEvaluator("all-MiniLM-L6-v2")
            metrics = evaluator.evaluate(original_text, summary)
            print(f"Quality score: {metrics['quality_score']:.3f}")
            ```
        """
        # Initialize ROUGE scorer
        self.rouge_scorer = rouge_score.scorer.RougeScorer(
            ROUGE_METRICS,
            use_stemmer=True  # Use stemming for better matching
        )
        
        # Store model name for lazy loading
        self._model_name = model_name
    
    @property
    @lru_cache(maxsize=1)
    def semantic_model(self) -> SentenceTransformer:
        """
        Lazy load semantic similarity model.
        
        Uses LRU cache to ensure the model is loaded only once
        per application lifecycle, improving performance and
        reducing memory usage.
        
        Returns:
            SentenceTransformer model instance
            
        Raises:
            Exception: If model loading fails
        """
        try:
            return SentenceTransformer(self._model_name)
        except Exception as e:
            raise Exception(
                f"Failed to load semantic model '{self._model_name}' / "
                f"Error al cargar modelo semántico '{self._model_name}': {str(e)}"
            )
    
    def _calculate_rouge_scores(
        self,
        original_text: str,
        summary: str
    ) -> dict[str, float]:
        """
        Calculate ROUGE scores for lexical overlap evaluation.
        
        Computes ROUGE-1, ROUGE-2, and ROUGE-L F-scores to measure
        lexical overlap between original text and summary.
        
        Args:
            original_text: Original input text
            summary: Generated summary
            
        Returns:
            Dictionary with ROUGE F-scores
            
        Example:
            ```python
            scores = evaluator._calculate_rouge_scores(text, summary)
            print(f"ROUGE-L: {scores['rouge_l']:.3f}")
            ```
        """
        try:
            scores = self.rouge_scorer.score(original_text, summary)
            
            return {
                "rouge_1": scores['rouge1'].fmeasure,
                "rouge_2": scores['rouge2'].fmeasure,
                "rouge_l": scores['rougeL'].fmeasure
            }
            
        except Exception as e:
            # Return zero scores if ROUGE calculation fails
            return {
                "rouge_1": 0.0,
                "rouge_2": 0.0,
                "rouge_l": 0.0
            }
    
    def _calculate_semantic_similarity(
        self,
        original_text: str,
        summary: str
    ) -> float:
        """
        Calculate semantic similarity using embeddings.
        
        Generates embeddings for both texts and computes cosine
        similarity to measure semantic overlap beyond lexical matching.
        
        Args:
            original_text: Original input text
            summary: Generated summary
            
        Returns:
            Cosine similarity score (0-1)
            
        Example:
            ```python
            similarity = evaluator._calculate_semantic_similarity(text, summary)
            print(f"Semantic similarity: {similarity:.3f}")
            ```
        """
        try:
            # Generate embeddings
            embeddings = self.semantic_model.encode([original_text, summary])
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(
                embeddings[0].reshape(1, -1),
                embeddings[1].reshape(1, -1)
            )
            
            # Extract similarity score
            similarity = float(similarity_matrix[0][0])
            
            # Ensure score is in valid range
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            # Return neutral score if semantic calculation fails
            return 0.5
    
    def _calculate_compression_ratio(
        self,
        original_text: str,
        summary: str
    ) -> float:
        """
        Calculate compression ratio and quality score.
        
        Computes the ratio of summary length to original length
        and evaluates how close it is to the ideal compression ratio.
        
        Args:
            original_text: Original input text
            summary: Generated summary
            
        Returns:
            Compression ratio (0-1)
            
        Example:
            ```python
            ratio = evaluator._calculate_compression_ratio(text, summary)
            print(f"Compression ratio: {ratio:.3f}")
            ```
        """
        try:
            # Count words in both texts
            original_words = len(original_text.split())
            summary_words = len(summary.split())
            
            if original_words == 0:
                return 0.0
            
            # Calculate compression ratio
            compression_ratio = summary_words / original_words
            
            return compression_ratio
            
        except Exception:
            # Return neutral ratio if calculation fails
            return IDEAL_COMPRESSION_RATIO
    
    def _calculate_compression_score(self, compression_ratio: float) -> float:
        """
        Calculate compression quality score.
        
        Evaluates how close the compression ratio is to the ideal
        range, penalizing ratios that are too high or too low.
        
        Args:
            compression_ratio: Ratio of summary to original length
            
        Returns:
            Compression quality score (0-1)
        """
        # Calculate distance from ideal ratio
        distance = abs(IDEAL_COMPRESSION_RATIO - compression_ratio)
        
        # Normalize distance to score (within tolerance = 1.0, outside = decreasing)
        if distance <= COMPRESSION_TOLERANCE:
            score = 1.0
        else:
            # Linear decrease beyond tolerance
            max_distance = IDEAL_COMPRESSION_RATIO  # Maximum possible distance
            score = max(0.0, 1.0 - (distance - COMPRESSION_TOLERANCE) / max_distance)
        
        return score
    
    def _calculate_quality_score(
        self,
        rouge_l: float,
        semantic_similarity: float,
        compression_score: float
    ) -> float:
        """
        Calculate composite quality score.
        
        Combines individual metrics into a single quality score
        using weighted averaging based on importance.
        
        Args:
            rouge_l: ROUGE-L F-score
            semantic_similarity: Semantic similarity score
            compression_score: Compression quality score
            
        Returns:
            Composite quality score (0-1)
        """
        # Weighted combination
        quality_score = (
            self.ROUGE_L_WEIGHT * rouge_l +
            self.SEMANTIC_WEIGHT * semantic_similarity +
            self.COMPRESSION_WEIGHT * compression_score
        )
        
        # Ensure score is in valid range
        return max(0.0, min(1.0, quality_score))
    
    def evaluate(self, original_text: str, summary: str) -> EvaluationMetrics:
        """
        Evaluate summary quality with comprehensive metrics.
        
        Performs complete evaluation using multiple complementary
        metrics to assess summary quality across different dimensions.
        Provides detailed metrics for analysis and monitoring.
        
        Args:
            original_text: Original input text
            summary: Generated summary to evaluate
            
        Returns:
            EvaluationMetrics with comprehensive quality assessment
            
        Raises:
            ValueError: If input texts are empty or invalid
            
        Example:
            ```python
            evaluator = SummaryEvaluator()
            metrics = evaluator.evaluate(
                original_text="Long article about AI...",
                summary="AI is transforming industries..."
            )
            
            print(f"ROUGE-L: {metrics['rouge_l_f']:.3f}")
            print(f"Semantic similarity: {metrics['semantic_similarity']:.3f}")
            print(f"Quality score: {metrics['quality_score']:.3f}")
            ```
        """
        # Validate inputs
        if not original_text or not original_text.strip():
            raise ValueError(
                "Original text cannot be empty / Texto original no puede estar vacío"
            )
        
        if not summary or not summary.strip():
            raise ValueError(
                "Summary cannot be empty / Resumen no puede estar vacío"
            )
        
        # Calculate individual metrics
        rouge_scores = self._calculate_rouge_scores(original_text, summary)
        semantic_similarity = self._calculate_semantic_similarity(original_text, summary)
        compression_ratio = self._calculate_compression_ratio(original_text, summary)
        
        # Calculate compression quality score
        compression_score = self._calculate_compression_score(compression_ratio)
        
        # Calculate composite quality score
        quality_score = self._calculate_quality_score(
            rouge_scores["rouge_l"],
            semantic_similarity,
            compression_score
        )
        
        # Build comprehensive metrics
        metrics = EvaluationMetrics(
            rouge_1_f=round(rouge_scores["rouge_1"], 4),
            rouge_2_f=round(rouge_scores["rouge_2"], 4),
            rouge_l_f=round(rouge_scores["rouge_l"], 4),
            semantic_similarity=round(semantic_similarity, 4),
            compression_ratio=round(compression_ratio, 4),
            quality_score=round(quality_score, 4)
        )
        
        return metrics
    
    def get_quality_level(self, quality_score: float) -> str:
        """
        Get quality level description based on score.
        
        Provides human-readable quality assessment based on
        the composite quality score.
        
        Args:
            quality_score: Composite quality score (0-1)
            
        Returns:
            Quality level description
            
        Example:
            ```python
            level = evaluator.get_quality_level(0.85)
            print(f"Quality level: {level}")  # "High"
            ```
        """
        if quality_score >= 0.8:
            return "High / Alta"
        elif quality_score >= 0.6:
            return "Medium / Media"
        elif quality_score >= 0.4:
            return "Low / Baja"
        else:
            return "Poor / Pobre"
    
    def __repr__(self) -> str:
        """
        String representation of the evaluator.
        
        Returns:
            String representation with evaluator details
        """
        return f"SummaryEvaluator(model={self._model_name})"


# Export for easy importing
__all__ = ["SummaryEvaluator", "EvaluationMetrics"]
