"""Semantic embedding wrapper using spaCy's pretrained word vectors
(en_core_web_md). Used to semantically compare a student's profile against
each scheme's `searchable_text`, so relevant-but-not-exact matches still
surface (per the Setu abstract: "surfacing not just exact fits but close,
easily-overlooked matches").

Word vectors (rather than a transformer sentence-embedding model) are used
here because they run fully offline once the spaCy model is installed via
`python -m spacy download en_core_web_md` -- no external API/model-hub call
needed at request time, which also reinforces the privacy-first design.

Fallback: if en_core_web_md is unavailable, falls back to en_core_web_sm
(no word vectors → zero vectors → semantic score is neutral 0.5).
"""

import threading

import numpy as np
import spacy

_MODEL_PRIORITY = ["en_core_web_md", "en_core_web_sm"]
_nlp = None
_lock = threading.Lock()


def get_nlp():
    """Return the spaCy model, loading it once in a thread-safe manner.

    Tries models in priority order; falls back to a blank pipeline with a
    sentencizer if none are installed so the application stays usable.
    """
    global _nlp
    if _nlp is not None:
        return _nlp
    with _lock:
        if _nlp is not None:  # double-checked locking
            return _nlp
        for model_name in _MODEL_PRIORITY:
            try:
                _nlp = spacy.load(model_name)
                return _nlp
            except OSError:
                continue
        # Last resort: blank pipeline — semantic scores will all be 0
        _nlp = spacy.blank("en")
        _nlp.add_pipe("sentencizer")
    return _nlp


def embed_texts(texts: list[str]) -> np.ndarray:
    nlp = get_nlp()
    vectors = np.array([nlp(text).vector for text in texts], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero for zero-vectors (blank model fallback)
    norms[norms == 0] = 1e-8
    return vectors / norms


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two L2-normalised vectors = cosine similarity in [-1, 1]."""
    return float(np.dot(a, b))
