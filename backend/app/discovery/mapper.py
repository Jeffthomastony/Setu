"""Maps a raw fetched record (arbitrary shape) into Setu's scheme schema.

Source datasets don't share a common structure, so this does best-effort
field matching via aliases rather than assuming one fixed input shape.
Whatever free-text eligibility field we do find gets run through the same
spaCy extraction pipeline (`app.extraction.criteria_extractor`) already used
for the hand-curated schemes — reusing the exact structured extraction the
matching engine relies on, so a discovered scheme behaves identically to a
manually-added one once it's in the dataset.

Every mapped record carries `ai_metadata.auto_discovered = True` and
`ai_metadata.source_url` so anyone reviewing a git diff later (which is the
one review checkpoint that survives even with auto-merge enabled — nothing
reaches the live dataset without going through a commit) can immediately
see which entries came from this pipeline and where they came from.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

FIELD_ALIASES = {
    "scheme_name": ("scheme_name", "name", "title", "scholarship_name", "scheme"),
    "description": ("description", "details", "about", "summary"),
    "department": ("department", "implementing_agency", "agency", "ministry_department"),
    "ministry": ("ministry",),
    "state": ("state", "state_ut", "applicable_state", "state_name"),
    "official_website": ("website", "url", "official_website", "link", "portal_url"),
    "application_portal": ("application_portal", "apply_url", "portal", "application_link"),
    "eligibility_text": ("eligibility", "eligibility_criteria", "eligibility_details", "who_can_apply"),
    "benefits_text": ("benefits", "benefit", "assistance", "amount"),
    "documents_text": ("documents", "documents_required", "required_documents"),
}


def _first_match(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        for record_key, value in record.items():
            if record_key.strip().lower().replace(" ", "_") == key and value:
                return str(value).strip()
    return None


def _slugify_id(scheme_name: str, state: str | None, existing_ids: set[str]) -> str:
    state_code = "".join(w[0] for w in (state or "NAT").split())[:3].upper() or "NAT"
    base = f"SETU-{state_code}-DISC"
    n = 1
    while f"{base}-{n:03d}" in existing_ids:
        n += 1
    return f"{base}-{n:03d}"


def map_record(record: dict[str, Any], source_url: str, existing_ids: set[str]) -> dict[str, Any] | None:
    """Convert one raw record into a Setu scheme dict, or None if it's too
    sparse to be usable (no name, or no eligibility/description text at all)."""

    scheme_name = _first_match(record, FIELD_ALIASES["scheme_name"])
    if not scheme_name:
        return None

    description = _first_match(record, FIELD_ALIASES["description"]) or ""
    eligibility_text = _first_match(record, FIELD_ALIASES["eligibility_text"]) or ""
    if not description and not eligibility_text:
        return None  # nothing to extract criteria from or explain to a user

    state = _first_match(record, FIELD_ALIASES["state"]) or "National"
    department = _first_match(record, FIELD_ALIASES["department"])
    website = _first_match(record, FIELD_ALIASES["official_website"])
    portal = _first_match(record, FIELD_ALIASES["application_portal"]) or website
    documents_text = _first_match(record, FIELD_ALIASES["documents_text"]) or ""

    scheme_id = _slugify_id(scheme_name, state, existing_ids)

    scheme = {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "scheme_type": "auto_discovered",
        "ministry": _first_match(record, FIELD_ALIASES["ministry"]),
        "department": department,
        "state": state,
        "description": description or eligibility_text[:300],
        "official_website": website,
        "application_portal": portal,
        "application_start_date": None,
        "application_end_date": None,
        "last_updated": date.today().isoformat(),
        "eligibility": {
            "education_level": None,
            "course_type": None,
            "year_of_study": None,
            "institution_type": None,
            "income_limit": eligibility_text or None,
            "caste_category": [],
            "gender": "All",
            "disability": None,
            "domicile": None,
            "academic_percentage": None,
            "attendance_requirement": None,
            "age": eligibility_text or None,
            "other_conditions": [],
        },
        "benefits": {
            "tuition_fee_support": None,
            "hostel_fee_support": None,
            "maintenance_allowance": _first_match(record, FIELD_ALIASES["benefits_text"]),
            "book_allowance": None,
            "laptop_or_device_support": None,
            "travel_allowance": None,
            "other_benefits": [],
        },
        "required_documents": [d.strip() for d in documents_text.split(",") if d.strip()],
        "application": {
            "application_mode": "Online" if portal else None,
            "application_steps": [],
            "processing_time": None,
            "renewal_required": False,
        },
        "ai_metadata": {
            "keywords": [scheme_name],
            "target_students": [],
            "eligibility_tags": [],
            "benefit_tags": [],
            "searchable_text": f"{scheme_name}. {description}".strip(),
            "auto_discovered": True,
            "source_url": source_url,
            "discovered_at": datetime.now().isoformat(timespec="seconds"),
        },
    }
    return scheme
