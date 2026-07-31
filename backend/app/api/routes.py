import json
from pathlib import Path

from fastapi import APIRouter

from app.matching.embedder import cosine_similarity, embed_texts
from app.matching.matcher import match_student
from app.models import MatchResult, SchemeSearchResult, StudentProfile

router = APIRouter()

SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_schemes_cache: list[dict] | None = None

MIN_MATCH_SCORE = 70.0


def load_schemes() -> list[dict]:
    global _schemes_cache
    if _schemes_cache is None:
        with open(SCHEMES_PATH, encoding="utf-8") as f:
            _schemes_cache = json.load(f)
    return _schemes_cache


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/schemes")
def list_schemes():
    """Lightweight listing, used for admin/debug views (not the match flow)."""
    return [
        {"scheme_id": s["scheme_id"], "scheme_name": s["scheme_name"], "state": s["state"]}
        for s in load_schemes()
    ]


@router.get("/search", response_model=list[SchemeSearchResult])
def search_schemes(q: str):
    """Keyword search over schemes using semantic embeddings, with an exact
    keyword-hit boost so short acronyms (e.g. "NMMS") still surface strongly
    even though word-vector similarity alone handles those poorly.
    """
    query = q.strip()
    if not query:
        return []

    schemes = load_schemes()
    scheme_texts = [f"{s['scheme_name']}. {s['ai_metadata']['searchable_text']}" for s in schemes]
    embeddings = embed_texts([query] + scheme_texts)
    query_vec, scheme_vecs = embeddings[0], embeddings[1:]

    results = []
    for scheme, vec in zip(schemes, scheme_vecs):
        sim = cosine_similarity(query_vec, vec)
        relevance = max(0.0, min(1.0, (sim + 1) / 2)) * 100

        query_lower = query.lower()
        keyword_hit = query_lower in scheme["scheme_name"].lower() or any(
            query_lower in kw.lower() for kw in scheme["ai_metadata"].get("keywords", [])
        )
        if keyword_hit:
            relevance = max(relevance, 95.0)

        results.append(
            SchemeSearchResult(
                scheme_id=scheme["scheme_id"],
                scheme_name=scheme["scheme_name"],
                department=scheme.get("department"),
                state=scheme["state"],
                description=scheme["description"],
                relevance_score=round(relevance, 1),
                required_documents=scheme.get("required_documents", []),
                official_website=scheme.get("official_website"),
                application_portal=scheme.get("application_portal"),
            )
        )

    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results[:10]


@router.post("/match", response_model=list[MatchResult])
def match(student: StudentProfile):
    """Match a student profile against all known schemes.

    The student profile is used only in-memory for this request and is never
    persisted or logged, per Setu's privacy-first design.

    Only schemes scoring at or above MIN_MATCH_SCORE are returned, so
    students see confident matches rather than every low-relevance scheme.
    """
    schemes = load_schemes()
    results = match_student(student, schemes)
    return [r for r in results if r.overall_score >= MIN_MATCH_SCORE]
