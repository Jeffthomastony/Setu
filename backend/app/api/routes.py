import json
from pathlib import Path

from fastapi import APIRouter

from app.matching.matcher import match_student
from app.models import MatchResult, StudentProfile

router = APIRouter()

SCHEMES_PATH = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
_schemes_cache: list[dict] | None = None


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


@router.post("/match", response_model=list[MatchResult])
def match(student: StudentProfile):
    """Match a student profile against all known schemes.

    The student profile is used only in-memory for this request and is never
    persisted or logged, per Setu's privacy-first design.
    """
    schemes = load_schemes()
    return match_student(student, schemes)
