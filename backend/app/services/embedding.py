"""NileOps Semantic Embedding Service.

Provides bilingual (Arabic & English) embedding generation with pluggable backends:
- "e5": intfloat/multilingual-e5-small (384 dimensions, normalized, query/passage prefixes)
- "hash": Deterministic feature-hashing fallback (384 dimensions, normalized)
"""

import hashlib
import logging
import os
import re
import sys
from typing import List, Optional
import httpx
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Arabic diacritics regex
ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")

# Dynamic embedding dimension
DEFAULT_EMBEDDING_DIM = 384


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for resilient banking search."""
    # Remove diacritics
    text = ARABIC_DIACRITICS.sub("", text)
    # Normalize Alef forms
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize Teh Marbuta
    text = re.sub(r"ة", "ه", text)
    # Normalize Alef Maqsura to Ya
    text = re.sub(r"ى", "ي", text)
    return text.strip().lower()


def normalize_text(text: str) -> str:
    """Normalize multilingual text."""
    normalized_ar = normalize_arabic(text)
    # Collapse multiple whitespaces
    return re.sub(r"\s+", " ", normalized_ar).strip()


class EmbeddingService:
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIM):
        self.dimension = dimension
        self.backend = getattr(settings, "EMBEDDING_BACKEND", "e5").lower()
        self._model = None
        self._initialized = False

        # Pre-generate deterministic projection weights for semantic representation (hash fallback)
        rng = np.random.RandomState(42)
        proj = rng.randn(4096, self.dimension)
        q, _ = np.linalg.qr(proj)
        self.proj = q

        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize the configured embedding backend with graceful fallback."""
        if self.backend == "e5":
            try:
                # Ensure offline environment is respected
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

                # Workaround for Windows Code Integrity / Smart App Control blocking _regex.pyd
                if "regex" not in sys.modules:
                    sys.modules["regex"] = re

                from sentence_transformers import SentenceTransformer

                model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-small")
                logger.info("Loading E5 embedding model: %s", model_name)
                self._model = SentenceTransformer(
                    model_name,
                    local_files_only=True,
                )
                dim = (
                    self._model.get_embedding_dimension()
                    if hasattr(self._model, "get_embedding_dimension")
                    else self._model.get_sentence_embedding_dimension()
                )
                self.dimension = dim
                self._initialized = True
                logger.info("E5 embedding model loaded successfully. Dimension: %d", self.dimension)
            except Exception as e:
                logger.warning(
                    "Failed to load E5 model (%s). Falling back to deterministic hash backend.",
                    e,
                )
                self.backend = "hash"
                self._model = None
                self.dimension = DEFAULT_EMBEDDING_DIM
        else:
            self.backend = "hash"
            self._model = None
            self.dimension = DEFAULT_EMBEDDING_DIM

    async def probe_dimension(self) -> int:
        """Dynamically probe or return the active embedding dimension."""
        if self.backend == "e5" and self._model is not None:
            return self.dimension

        # Attempt Ollama if configured and reachable
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_URL}/api/embeddings",
                    json={"model": settings.OLLAMA_MODEL, "prompt": "dimension_probe"},
                )
                if res.status_code == 200:
                    vec = res.json().get("embedding", [])
                    if vec and len(vec) > 0:
                        self.dimension = len(vec)
                        return self.dimension
        except Exception:
            pass

        self.dimension = DEFAULT_EMBEDDING_DIM
        return self.dimension

    def _generate_dense_vector(self, text: str) -> List[float]:
        """Generate high-quality, normalized dense vector for Arabic & English text via feature hashing."""
        norm_text = normalize_text(text)
        if not norm_text:
            return [0.0] * self.dimension

        tokens = norm_text.split()
        features = list(tokens)

        for word in tokens:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    features.append(word[i : i + 3])

        bow = np.zeros(4096, dtype=np.float32)
        for feat in features:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest()[:8], 16) % 4096
            bow[h] += 1.0

        bow = np.log1p(bow)
        dense = np.dot(bow, self.proj)

        norm = np.linalg.norm(dense)
        if norm > 0:
            dense = dense / norm

        return dense.tolist()

    def _prepare_text_e5(self, text: str, is_query: bool) -> str:
        """Prepare text for E5 embedding with prefix and Arabic normalization."""
        norm = normalize_text(text)
        prefix = "query: " if is_query else "passage: "
        return f"{prefix}{norm}"

    async def get_embedding(self, text: str, is_query: bool = True) -> List[float]:
        """Generate embedding vector for a single text."""
        if self.backend == "e5" and self._model is not None:
            try:
                prepped = self._prepare_text_e5(text, is_query=is_query)
                emb = self._model.encode(prepped, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.warning("E5 encode failed (%s), falling back to hash", e)
                return self._generate_dense_vector(text)
        return self._generate_dense_vector(text)

    async def get_embeddings(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """Batch embedding generation."""
        if self.backend == "e5" and self._model is not None:
            try:
                prepped_list = [self._prepare_text_e5(t, is_query=is_query) for t in texts]
                embs = self._model.encode(prepped_list, normalize_embeddings=True)
                return embs.tolist()
            except Exception as e:
                logger.warning("E5 batch encode failed (%s), falling back to hash", e)
                return [self._generate_dense_vector(t) for t in texts]
        return [self._generate_dense_vector(t) for t in texts]


embedding_service = EmbeddingService()
