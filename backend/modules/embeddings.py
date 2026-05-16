"""
modules/embeddings.py
Semantic similarity using TF-IDF + cosine similarity (scikit-learn).
Lightweight alternative to sentence-transformers — no PyTorch needed.
"""
import re
import numpy as np
from collections import Counter
from typing import List, Dict, Any

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SK = True
except ImportError:
    _SK = False


class EmbeddingEngine:
    def __init__(self):
        self._vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        ) if _SK else None

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between resume and job description."""
        if _SK and self._vectorizer:
            try:
                tfidf = self._vectorizer.fit_transform([text_a, text_b])
                sim   = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
                return float(sim)
            except Exception:
                pass
        # Fallback — simple word overlap
        return self._word_overlap(text_a, text_b)

    def encode(self, text: str) -> np.ndarray:
        words = re.findall(r"[a-zA-Z]{2,}", text.lower())
        freq  = Counter(words)
        vec   = np.array(list(freq.values()), dtype=np.float32)
        n     = np.linalg.norm(vec)
        return vec / n if n else vec

    def _word_overlap(self, text_a: str, text_b: str) -> float:
        words_a = set(re.findall(r"[a-zA-Z]{3,}", text_a.lower()))
        words_b = set(re.findall(r"[a-zA-Z]{3,}", text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / (len(words_a | words_b))
