"""Quick manual sanity check for the extraction + matching pipeline.
Run with: python scripts/test_matching.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.matching.matcher import match_student
from app.models import StudentProfile

SCHEMES_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "schemes.json"
schemes = json.loads(SCHEMES_PATH.read_text(encoding="utf-8"))

profiles = {
    "OBC post-matric student, low income (should match e-Grantz well)": StudentProfile(
        age=19,
        family_income=80000,
        category="OBC",
        state="Kerala",
        residence_area="rural",
        education_level="Undergraduate",
        academic_percentage=70,
        parent_status="both_parents",
        gender="female",
        disability=False,
    ),
    "Class 8 SC student, meets NMMS criteria": StudentProfile(
        age=13,
        family_income=200000,
        category="SC",
        state="Kerala",
        residence_area="rural",
        education_level="Class 8",
        academic_percentage=60,
        parent_status="both_parents",
        gender="male",
        disability=False,
    ),
    "Orphan, Class 6-7, low income (should match Snehapoorvam)": StudentProfile(
        age=12,
        family_income=15000,
        category="General",
        state="Kerala",
        residence_area="rural",
        education_level="Class 6-7",
        academic_percentage=None,
        parent_status="orphan",
        gender="female",
        disability=False,
    ),
    "Out-of-state student (should score low on all)": StudentProfile(
        age=20,
        family_income=90000,
        category="SC",
        state="Tamil Nadu",
        residence_area="urban",
        education_level="Undergraduate",
        academic_percentage=75,
        parent_status="both_parents",
        gender="male",
        disability=False,
    ),
}

for label, profile in profiles.items():
    print(f"\n=== {label} ===")
    results = match_student(profile, schemes)
    for r in results:
        print(f"  {r.scheme_name}: overall={r.overall_score} criteria={r.criteria_score} semantic={r.semantic_score}")
        for c in r.criteria_breakdown:
            mark = "✅" if c.matched else "❌"
            print(f"      {mark} {c.criterion}: {c.reason}")
