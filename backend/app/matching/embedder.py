"""Semantic embedding wrapper using spaCy's pretrained word vectors
(en_core_web_md). Used to semantically compare a student's profile against
each scheme's `searchable_text`, so relevant-but-not-exact matches still
surface (per the Setu abstract: "surfacing not just exact fits but close,
easily-overlooked matches").

Word vectors (rather than a transformer sentence-embedding model) are used
here because they run fully offline once the spaCy model is installed via
`python -m spacy download en_core_web_md` -- no external API/model-hub call
needed at request time, which also reinforces the privacy-first design.
"""

import numpy as np
import spacy

_MODEL_NAME = "en_core_web_md"
_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(_MODEL_NAME)
    return _nlp


def embed_texts(texts: list[str]) -> np.ndarray:
    nlp = get_nlp()
    vectors = np.array([nlp(text).vector for text in texts], dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    return vectors / norms


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))
