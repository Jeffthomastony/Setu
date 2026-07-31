"""Semantic embedding wrapper using a pretrained sentence-transformer model
(all-MiniLM-L6-v2, via Hugging Face's `sentence-transformers` library). Used
to semantically compare a student's profile / search query against each
scheme's `searchable_text`, so relevant-but-not-exact matches still surface
(per the Setu abstract: "surfacing not just exact fits but close,
easily-overlooked matches").

A transformer sentence-embedding model is used here (rather than averaging
static spaCy word vectors) because it produces genuinely contextual sentence
embeddings — e.g. it captures that "help for disabled students" and
"scholarship for persons with disabilities" are semantically close even with
almost no literal word overlap, which plain word-vector averaging handles
far more weakly.

The model is downloaded once from the Hugging Face model hub (cached locally
under `~/.cache/huggingface`, ~90MB) and then runs fully offline, entirely on
this machine, at request time — preserving Setu's privacy-first design; no
student data or query text is ever sent to an external API.

Fallback: if the model can't be loaded (e.g. no internet on first run and no
local cache), embeddings degrade to zero vectors so cosine similarity is
always neutral (0) rather than the app crashing.
"""

import threading

import numpy as np

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
_load_failed = False
_lock = threading.Lock()


def get_model():
    """Return the sentence-transformer model, loading it once, thread-safely.

    Returns None if the model could not be loaded, so callers can fall back
    gracefully instead of crashing.
    """
    global _model, _load_failed
    if _model is not None or _load_failed:
        return _model
    with _lock:
        if _model is not None or _load_failed:  # double-checked locking
            return _model
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_MODEL_NAME)
        except Exception:
            _load_failed = True
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    if model is None:
        # No model available — neutral zero vectors (all similarities become 0)
        return np.zeros((len(texts), 1), dtype=np.float32)
    vectors = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
    )
    return vectors.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two L2-normalised vectors = cosine similarity in [-1, 1]."""
    return float(np.dot(a, b))
