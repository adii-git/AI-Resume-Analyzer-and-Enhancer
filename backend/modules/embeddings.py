"""
modules/embeddings.py
Semantic similarity using sentence-transformers.
Falls back to TF-IDF cosine if library is missing.
"""
import re
import numpy as np
from collections import Counter
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    _ST = True
except Exception:
    _MODEL = None
    _ST = False

def _cos(a: np.ndarray, b: np.ndarray) -> float:
    # Make vectors the same length for fallback TF-IDF
    l = max(len(a), len(b))
    a = np.pad(a, (0, l-len(a)))
    b = np.pad(b, (0, l-len(b)))
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a,b)/d) if d else 0.0

class EmbeddingEngine:
    def encode(self, text: str) -> np.ndarray:
        if _ST and _MODEL:
            return _MODEL.encode(text, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        return self._tfidf(text)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        return _cos(self.encode(text_a), self.encode(text_b))

    def _tfidf(self, text: str) -> np.ndarray:
        words = re.findall(r"[a-zA-Z]{2,}", text.lower())
        freq  = Counter(words)
        vec   = np.array(list(freq.values()), dtype=np.float32)
        n     = np.linalg.norm(vec)
        return vec / n if n else vec
