"""Data-quality gate for scheme datasets.

Runs the real NLP extraction pipeline against every scheme in both datasets
and flags rows where a criterion field is present as free text but the
extractor came away with nothing structured from it — usually a sign the
text is phrased in a way the extractor's regexes don't recognise yet (this
script exists because that exact bug shipped once: several senior-citizen
schemes phrased age as "60 years and above" while the extractor only
recognised "above 60 years").

Also flags duplicate scheme_ids/names within a dataset, and IDs that already
exist in another dataset.

Run with: python scripts/validate_schemes.py
Exits non-zero if any problems are found, so it can be wired into CI.
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.extraction.criteria_extractor import extract_criteria

DATASETS = {
    "schemes.json": Path(__file__).resolve().parent.parent / "app" / "data" / "schemes.json",
    "senior_citizen_schemes.json": Path(__file__).resolve().parent.parent / "app" / "data" / "senior_citizen_schemes.json",
}


def check_dataset(name: str, path: Path, seen_ids: dict[str, str]) -> list[str]:
    problems: list[str] = []
    schemes = json.loads(path.read_text(encoding="utf-8"))

    ids = Counter(s["scheme_id"] for s in schemes)
    for scheme_id, count in ids.items():
        if count > 1:
            problems.append(f"[{name}] duplicate scheme_id '{scheme_id}' appears {count} times")

    names = Counter(s["scheme_name"] for s in schemes)
    for scheme_name, count in names.items():
        if count > 1:
            problems.append(f"[{name}] duplicate scheme_name '{scheme_name}' appears {count} times")

    for scheme in schemes:
        scheme_id = scheme["scheme_id"]
        if scheme_id in seen_ids:
            problems.append(
                f"[{name}] scheme_id '{scheme_id}' also exists in {seen_ids[scheme_id]}"
            )
        seen_ids[scheme_id] = name

        elig = scheme.get("eligibility", {})
        criteria = extract_criteria(scheme)

        age_text = elig.get("age") or ""
        if age_text and criteria.min_age is None and criteria.max_age is None:
            problems.append(
                f"[{name}] {scheme_id}: age text {age_text!r} produced no min/max_age — "
                f"check it matches a recognised phrasing pattern"
            )

        income_text = elig.get("income_limit") or ""
        no_ceiling = (
            criteria.income_ceiling_general is None
            and not criteria.income_ceiling_by_category
            and not criteria.no_income_limit_categories
        )
        mentions_number = any(ch.isdigit() for ch in income_text)
        says_no_limit = "no income limit" in income_text.lower() or "no limit" in income_text.lower()
        if income_text and no_ceiling and mentions_number and not says_no_limit:
            problems.append(
                f"[{name}] {scheme_id}: income text {income_text!r} contains a number but no "
                f"ceiling was extracted — check the currency phrasing"
            )

        # Missing required official links
        if not scheme.get("official_website") or "example." in scheme.get("official_website", ""):
            problems.append(f"[{name}] {scheme_id}: missing or placeholder official_website")
        if not scheme.get("application_portal") or "example." in scheme.get("application_portal", ""):
            problems.append(f"[{name}] {scheme_id}: missing or placeholder application_portal")

    return problems


def main() -> int:
    seen_ids: dict[str, str] = {}
    all_problems: list[str] = []
    total = 0

    for name, path in DATASETS.items():
        schemes = json.loads(path.read_text(encoding="utf-8"))
        total += len(schemes)
        all_problems.extend(check_dataset(name, path, seen_ids))

    print(f"Validated {total} schemes across {len(DATASETS)} dataset(s).\n")

    if all_problems:
        print(f"FAILED — {len(all_problems)} problem(s) found:\n")
        for p in all_problems:
            print(f"  - {p}")
        return 1

    print("PASSED — no data-quality problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
