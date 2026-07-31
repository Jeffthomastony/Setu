import difflib
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.matching.matcher import match_student
from app.matching.embedder import cosine_similarity, embed_texts
from app.models import MatchResult, SchemeSearchResult, StudentProfile

router = APIRouter()

SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_schemes_cache: list[dict] | None = None

MIN_MATCH_SCORE = 70.0
MIN_SEARCH_SCORE = 30.0  # lower bar for keyword/semantic search

# Canonical list of Indian states and UTs used for fuzzy state normalization.
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
    "Daman and Diu", "Lakshadweep", "Puducherry",
]


def normalize_state(state: str) -> str:
    """Fuzzy-match user input to a canonical Indian state/UT name.

    Uses difflib's sequence matching with a 0.6 cutoff so common typos
    ('Kerla', 'Karnatka') and case variants ('kerala') resolve correctly.
    Falls back to the original string if no match is found above cutoff.
    """
    matches = difflib.get_close_matches(state.strip(), INDIAN_STATES, n=1, cutoff=0.6)
    return matches[0] if matches else state.strip()


def load_schemes() -> list[dict]:
    global _schemes_cache
    if _schemes_cache is None:
        with open(SCHEMES_PATH, encoding="utf-8") as f:
            _schemes_cache = json.load(f)
    return _schemes_cache


@router.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


@router.get("/schemes")
def list_schemes():
    """Lightweight listing — used for admin / debug views (not the match flow)."""
    return [
        {"scheme_id": s["scheme_id"], "scheme_name": s["scheme_name"], "state": s["state"]}
        for s in load_schemes()
    ]


@router.post("/match", response_model=list[MatchResult])
def match(student: StudentProfile):
    """Match a student profile against all known schemes.

    The student profile is used only in-memory for this request and is never
    persisted or logged, per Setu's privacy-first design.

    The student's state input is fuzzy-normalized (e.g. 'Kerla' → 'Kerala')
    before matching so minor typos don't silently produce zero results.

    Only schemes scoring at or above MIN_MATCH_SCORE are returned, so
    students see confident matches rather than every low-relevance scheme.
    """
    schemes = load_schemes()
    # AI step: normalize state before matching
    student = student.model_copy(update={"state": normalize_state(student.state)})
    try:
        results = match_student(student, schemes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Matching failed: {exc}") from exc
    return [r for r in results if r.overall_score >= MIN_MATCH_SCORE]


@router.get("/search", response_model=list[SchemeSearchResult])
def search(q: str = Query(..., min_length=1, description="Free-text search query")):
    """Semantic keyword search over the scheme catalogue.

    Combines:
    - Keyword matching against scheme name, department, description, and
      eligibility text (case-insensitive).
    - Semantic vector similarity via spaCy word embeddings.

    Returns up to 10 results, ranked by combined relevance score.
    """
    schemes = load_schemes()
    query_lower = q.lower()

    results: list[SchemeSearchResult] = []

    # Build searchable corpus for embedding
    scheme_texts = [
        s.get("ai_metadata", {}).get("searchable_text", s.get("scheme_name", ""))
        for s in schemes
    ]

    try:
        # Semantic similarity
        embeddings = embed_texts([q] + scheme_texts)
        query_vec = embeddings[0]
        scheme_vecs = embeddings[1:]
        semantic_scores = [
            float(cosine_similarity(query_vec, sv)) for sv in scheme_vecs
        ]
    except Exception:
        # Fallback: pure keyword matching if embedding fails
        semantic_scores = [0.0] * len(schemes)

    for scheme, sem_score in zip(schemes, semantic_scores):
        # Keyword score: check if query terms appear in various fields
        name = scheme.get("scheme_name", "").lower()
        dept = scheme.get("department", "").lower()
        desc = scheme.get("description", "").lower()
        elig_text = " ".join(
            str(v) for v in (scheme.get("eligibility") or {}).values()
        ).lower()
        searchable = " ".join([name, dept, desc, elig_text])

        # Score based on query term hits
        query_terms = [t for t in query_lower.split() if len(t) > 1]
        if query_terms:
            keyword_hits = sum(1 for term in query_terms if term in searchable)
            keyword_score = keyword_hits / len(query_terms)
        else:
            keyword_score = 1.0 if query_lower in searchable else 0.0

        # Normalize semantic score from [-1,1] → [0,1]
        sem_norm = max(0.0, min(1.0, (sem_score + 1) / 2))

        # Combined: 50% keyword, 50% semantic
        combined = round((0.5 * keyword_score + 0.5 * sem_norm) * 100, 1)

        if combined >= MIN_SEARCH_SCORE:
            results.append(
                SchemeSearchResult(
                    scheme_id=scheme["scheme_id"],
                    scheme_name=scheme["scheme_name"],
                    department=scheme.get("department"),
                    state=scheme.get("state", ""),
                    description=scheme.get("description", ""),
                    relevance_score=combined,
                    required_documents=scheme.get("required_documents", []),
                    official_website=scheme.get("official_website"),
                    application_portal=scheme.get("application_portal"),
                )
            )

    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results[:10]


@router.get("/ask/{scheme_id}")
def ask_scheme(
    scheme_id: str,
    q: str = Query(..., min_length=1, description="Free-text question about the scheme"),
):
    """Retrieval-grounded Q&A: answer a free-text question about one scheme.

    The answer is assembled entirely from the scheme's own structured data
    (eligibility, benefits, application process, documents) — the question
    is matched against generated fact sentences via semantic + keyword
    scoring, and the best-matching facts are returned verbatim. Nothing is
    freely generated, so every answer is traceable to a specific field in
    the scheme record.
    """
    from app.qa.qa_engine import answer_question

    schemes = load_schemes()
    scheme = next((s for s in schemes if s["scheme_id"] == scheme_id), None)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

    return answer_question(scheme, q)


@router.get("/explain/{scheme_id}")
def explain_scheme(scheme_id: str):
    """Generate a natural-language AI explanation of what a scheme is looking for.

    This endpoint surfaces the NLP extraction layer to the user: it takes the
    StructuredCriteria parsed from each scheme's free-text eligibility fields
    and synthesises them into a human-readable paragraph describing who the
    scheme targets — making the AI's understanding of the scheme transparent.
    """
    from app.extraction.criteria_extractor import extract_criteria

    schemes = load_schemes()
    scheme = next((s for s in schemes if s["scheme_id"] == scheme_id), None)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

    criteria = extract_criteria(scheme)

    # NLG: build a natural-language description from extracted criteria
    parts: list[str] = []

    if criteria.state:
        parts.append(f"for residents of {criteria.state}")

    if criteria.eligible_categories:
        cats = ", ".join(criteria.eligible_categories)
        parts.append(f"open to {cats} category students")
    else:
        parts.append("open to all categories")

    if criteria.no_income_limit_categories:
        parts.append(
            f"with no income ceiling for {', '.join(criteria.no_income_limit_categories)} students"
        )
    if criteria.income_ceiling_general is not None:
        parts.append(f"requiring annual family income below \u20b9{criteria.income_ceiling_general:,.0f}")
    elif criteria.income_ceiling_by_category:
        ceilings = "; ".join(
            f"{cat}: \u20b9{amt:,.0f}" for cat, amt in criteria.income_ceiling_by_category.items()
        )
        parts.append(f"with income limits — {ceilings}")

    if criteria.min_class is not None:
        if criteria.max_class and criteria.max_class >= 20:
            parts.append(f"for students in Class {criteria.min_class} through higher education")
        else:
            parts.append(f"for students in Class {criteria.min_class}\u2013{criteria.max_class}")

    if criteria.min_percentage_general is not None:
        threshold = f"{criteria.min_percentage_general:.0f}%"
        if criteria.min_percentage_sc_st and criteria.min_percentage_sc_st != criteria.min_percentage_general:
            parts.append(
                f"requiring a minimum academic score of {threshold} "
                f"({criteria.min_percentage_sc_st:.0f}% for SC/ST)"
            )
        else:
            parts.append(f"requiring a minimum academic score of {threshold}")

    if criteria.gender_restriction:
        parts.append(f"restricted to {criteria.gender_restriction} applicants")

    if criteria.min_age is not None and criteria.max_age is not None:
        parts.append(f"for students aged {criteria.min_age}\u2013{criteria.max_age}")
    elif criteria.max_age is not None:
        parts.append(f"for students under {criteria.max_age} years old")
    elif criteria.min_age is not None:
        parts.append(f"for students at least {criteria.min_age} years old")

    if criteria.requires_disability:
        parts.append("specifically for persons with a registered disability")

    if criteria.requires_orphan_or_single_parent:
        parts.append("targeting orphaned or single-parent children")

    if parts:
        explanation = (
            f"{scheme['scheme_name']} is a scheme {', '.join(parts)}."
        )
    else:
        explanation = (
            f"{scheme['scheme_name']} has broad eligibility with few specific restrictions "
            "— most students may qualify."
        )

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme.get("scheme_name"),
        "ai_explanation": explanation,
        "criteria_richness": sum([
            criteria.income_ceiling_general is not None,
            bool(criteria.income_ceiling_by_category),
            bool(criteria.no_income_limit_categories),
            criteria.min_class is not None,
            criteria.min_percentage_general is not None,
            bool(criteria.eligible_categories),
            criteria.gender_restriction is not None,
            criteria.min_age is not None or criteria.max_age is not None,
            criteria.requires_disability,
            criteria.requires_orphan_or_single_parent,
        ]),
        "description": scheme.get("description", ""),
    }