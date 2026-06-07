"""modules/embeddings.py — TF-IDF similarity (no heavy deps)"""
import re
import numpy as np
from collections import Counter
from typing import List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cos_sim
    _SK = True
except ImportError:
    _SK = False


class EmbeddingEngine:
    def __init__(self):
        self._vec = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1,2)) if _SK else None

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        if _SK and self._vec:
            try:
                tfidf = self._vec.fit_transform([text_a, text_b])
                return float(_cos_sim(tfidf[0:1], tfidf[1:2])[0][0])
            except Exception:
                pass
        return self._overlap(text_a, text_b)

    def _overlap(self, a: str, b: str) -> float:
        wa = set(re.findall(r"[a-zA-Z]{3,}", a.lower()))
        wb = set(re.findall(r"[a-zA-Z]{3,}", b.lower()))
        if not wa or not wb: return 0.0
        return len(wa & wb) / len(wa | wb)
