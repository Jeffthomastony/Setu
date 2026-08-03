"""Validation gate for auto-discovered scheme candidates.

Since candidates that pass this gate are merged straight into the live
dataset with no human review step, this is the *only* thing standing
between a bad candidate and something a real user sees. It's deliberately
stricter than the general-purpose `scripts/validate_schemes.py` checks,
because it's specifically designed to catch the failure modes that have
actually shown up in this project before:

  - Fake/placeholder/broken links               -> live HTTP reachability check
  - A discontinued scheme presented as live      -> keyword scan
  - The same real scheme added twice             -> fuzzy name dedup
  - Eligibility text that doesn't parse to rules -> reuses the extractor

A candidate is rejected if it fails ANY check — there's no partial credit,
because there's no human downstream to catch a partial failure.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

import requests

# Word-boundary regex for the "Rs" currency abbreviation — a bare substring
# check for "rs " false-positives inside ordinary words (e.g. "scholars above").
_RS_CURRENCY_RE = re.compile(r"\brs\.?\s*\d", re.IGNORECASE)

from app.extraction.criteria_extractor import extract_criteria

DISCONTINUED_KEYWORDS = (
    "discontinued", "closed to new", "no longer accept", "scrapped",
    "suspended", "withdrawn", "not accepting new applications",
    "scheme has ended", "no longer operational", "phased out",
)

DUPLICATE_NAME_SIMILARITY_THRESHOLD = 0.82


@dataclass
class GateResult:
    accepted: bool
    reasons: list[str] = field(default_factory=list)


def _check_urls_present_and_not_placeholder(scheme: dict) -> list[str]:
    """Static checks — no network needed, so these always run regardless of
    --skip-url-check (that flag only controls the live reachability check)."""
    problems = []
    for field_name in ("official_website", "application_portal"):
        url = scheme.get(field_name)
        if not url:
            problems.append(f"{field_name} is missing")
        elif "example." in url:
            problems.append(f"{field_name} is a placeholder URL ({url})")
    return problems


def _check_urls_reachable(scheme: dict) -> list[str]:
    problems = []
    for field_name in ("official_website", "application_portal"):
        url = scheme.get(field_name)
        if not url or "example." in url:
            continue  # already reported by _check_urls_present_and_not_placeholder
        try:
            resp = requests.head(url, timeout=8, allow_redirects=True)
            if resp.status_code >= 400:
                # Some government sites reject HEAD; retry with GET before failing
                resp = requests.get(url, timeout=8, allow_redirects=True, stream=True)
            if resp.status_code >= 400:
                problems.append(f"{field_name} returned HTTP {resp.status_code} ({url})")
        except requests.RequestException as exc:
            problems.append(f"{field_name} unreachable: {exc} ({url})")
    return problems


def _check_not_discontinued(scheme: dict) -> list[str]:
    text = " ".join(
        [
            scheme.get("description") or "",
            str(scheme.get("eligibility", {}).get("income_limit") or ""),
            str(scheme.get("eligibility", {}).get("age") or ""),
        ]
    ).lower()
    hits = [kw for kw in DISCONTINUED_KEYWORDS if kw in text]
    return [f"description/eligibility text mentions '{kw}' — likely discontinued" for kw in hits]


def _check_not_duplicate(scheme: dict, existing_schemes: list[dict]) -> list[str]:
    name = scheme["scheme_name"].lower()
    state = (scheme.get("state") or "").lower()
    for existing in existing_schemes:
        if (existing.get("state") or "").lower() != state:
            continue
        similarity = difflib.SequenceMatcher(None, name, existing["scheme_name"].lower()).ratio()
        if similarity >= DUPLICATE_NAME_SIMILARITY_THRESHOLD:
            return [
                f"looks like a duplicate of existing scheme '{existing['scheme_name']}' "
                f"({existing['scheme_id']}), name similarity {similarity:.2f}"
            ]
    return []


def _check_criteria_extractable(scheme: dict) -> list[str]:
    problems = []
    elig = scheme.get("eligibility", {})
    criteria = extract_criteria(scheme)

    age_text = elig.get("age") or ""
    if age_text and criteria.min_age is None and criteria.max_age is None:
        problems.append(f"age text {age_text!r} didn't parse into a usable rule")

    income_text = elig.get("income_limit") or ""
    # Only judge this as an income-parsing failure if the text is actually
    # about income — the generic discovery mapper puts the same raw
    # eligibility blurb into both income_limit and age, so a pure age
    # sentence with no income content at all shouldn't be flagged here.
    mentions_income = (
        any(kw in income_text.lower() for kw in ("income", "earn", "salary", "₹"))
        or bool(_RS_CURRENCY_RE.search(income_text))
    )
    no_ceiling = (
        criteria.income_ceiling_general is None
        and not criteria.income_ceiling_by_category
        and not criteria.no_income_limit_categories
    )
    says_no_limit = "no income limit" in income_text.lower() or "no limit" in income_text.lower()
    if income_text and mentions_income and no_ceiling and any(ch.isdigit() for ch in income_text) and not says_no_limit:
        problems.append(f"income text {income_text!r} didn't parse into a usable ceiling")

    return problems


def run_gate(scheme: dict, existing_schemes: list[dict], check_urls: bool = True) -> GateResult:
    """Run every safety check. check_urls=False skips the live network check
    (useful for offline testing of the rest of the pipeline)."""
    reasons: list[str] = []

    if not scheme.get("scheme_name") or not scheme.get("description"):
        reasons.append("missing scheme_name or description")

    reasons.extend(_check_not_discontinued(scheme))
    reasons.extend(_check_not_duplicate(scheme, existing_schemes))
    reasons.extend(_check_criteria_extractable(scheme))
    reasons.extend(_check_urls_present_and_not_placeholder(scheme))
    if check_urls:
        reasons.extend(_check_urls_reachable(scheme))

    return GateResult(accepted=len(reasons) == 0, reasons=reasons)
