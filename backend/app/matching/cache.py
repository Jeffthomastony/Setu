"""Startup cache for scheme criteria and embeddings.

Both `extract_all` (spaCy NLP) and `embed_texts` (sentence-transformer) are
expensive operations.  Because scheme files (student and senior citizen) don't
change at runtime, we cache extracted criteria by scheme_id and cache scheme
embeddings by scheme-ID tuple in module-level memory.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from app.extraction.criteria_extractor import StructuredCriteria

_lock = threading.Lock()

# Keyed by scheme_id → StructuredCriteria (supports both student and senior schemes)
_criteria_cache: dict[str, "StructuredCriteria"] = {}

# Keyed by tuple of scheme_ids → np.ndarray of embeddings
_embedding_cache: dict[tuple[str, ...], np.ndarray] = {}


def get_criteria(schemes: list[dict]) -> dict[str, "StructuredCriteria"]:
    """Return (cached) structured-criteria extraction for all schemes in the list."""
    missing = [s for s in schemes if s["scheme_id"] not in _criteria_cache]
    if missing:
        with _lock:
            missing_again = [s for s in missing if s["scheme_id"] not in _criteria_cache]
            if missing_again:
                from app.extraction.criteria_extractor import extract_all
                extracted = extract_all(missing_again)
                _criteria_cache.update(extracted)

    return {s["scheme_id"]: _criteria_cache[s["scheme_id"]] for s in schemes}


def get_scheme_embeddings(schemes: list[dict]) -> np.ndarray:
    """Return (cached) embedding matrix for all scheme searchable texts.

    Shape: (len(schemes), embedding_dim).
    """
    key = tuple(s["scheme_id"] for s in schemes)
    if key in _embedding_cache:
        return _embedding_cache[key]

    with _lock:
        if key in _embedding_cache:
            return _embedding_cache[key]
        from app.matching.embedder import embed_texts
        texts = [s["ai_metadata"]["searchable_text"] for s in schemes]
        embeddings = embed_texts(texts)
        _embedding_cache[key] = embeddings

    return _embedding_cache[key]


def invalidate() -> None:
    """Clear all caches — useful for tests or hot-reload scenarios."""
    global _criteria_cache, _embedding_cache
    with _lock:
        _criteria_cache.clear()
        _embedding_cache.clear()
