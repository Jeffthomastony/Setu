"""Matching engine: combines hard eligibility-criteria checks (from the NLP
extraction step) with semantic similarity (embeddings) into a ranked,
explainable list of scheme matches for a student.

Scoring uses **adaptive weighting**: the more structured criteria fields were
successfully extracted for a scheme, the more the criteria score is trusted
relative to the semantic embedding score. Schemes with sparse criteria data
(e.g., no income limit or class-range specified) lean more heavily on semantic
similarity so the AI model compensates for the missing structure.
"""

from app.extraction.criteria_extractor import StructuredCriteria, extract_all
from app.matching.embedder import cosine_similarity, embed_texts
from app.models import CriterionCheck, MatchResult, StudentProfile

# Approximate numeric class for each schooling-stage education level, used to
# compare against a scheme's parsed min_class/max_class range.
EDUCATION_LEVEL_TO_CLASS_RANGE = {
    "Class 1-5": (1, 5),
    "Class 6-7": (6, 7),
    "Class 8": (8, 8),
    "Class 9-10": (9, 10),
    "Class 11-12": (11, 12),
}

# Keywords used to match post-matric levels against a scheme's free-text
# education_level description when there's no numeric class range to compare.
EDUCATION_LEVEL_KEYWORDS = {
    "Class 11-12": {"higher", "secondary", "vhse", "class"},
    "ITI": {"iti", "vocational"},
    "Polytechnic/Diploma": {"polytechnic", "diploma"},
    "Undergraduate": {"undergraduate", "graduation", "degree"},
    "Postgraduate": {"postgraduate", "graduation", "degree"},
    "Professional": {"professional"},
    "Doctoral": {"doctoral", "phd"},
}


# ── Individual criterion checkers ──────────────────────────────────────────────

def _check_state(student: StudentProfile, criteria: StructuredCriteria) -> CriterionCheck:
    if not criteria.state or criteria.state.lower() in ("national", "all", "india", "pan india"):
        return CriterionCheck(criterion="State", matched=True, reason="No state restriction — open to all states")
    matched = student.state.strip().lower() == criteria.state.strip().lower()
    reason = (
        f"Scheme is for residents of {criteria.state}"
        if matched
        else f"Scheme is limited to {criteria.state}; student is from {student.state}"
    )
    return CriterionCheck(criterion="State", matched=matched, reason=reason)


def _check_category(student: StudentProfile, criteria: StructuredCriteria) -> CriterionCheck:
    if not criteria.eligible_categories:
        return CriterionCheck(criterion="Category", matched=True, reason="Open to all categories")
    matched = student.category.upper() in criteria.eligible_categories
    reason = (
        f"{student.category} is an eligible category"
        if matched
        else f"Scheme is limited to {', '.join(criteria.eligible_categories)}"
    )
    return CriterionCheck(criterion="Category", matched=matched, reason=reason)


def _check_income(student: StudentProfile, criteria: StructuredCriteria) -> CriterionCheck:
    category = student.category.upper()

    if category in [c.upper() for c in criteria.no_income_limit_categories]:
        return CriterionCheck(
            criterion="Family income", matched=True, reason=f"No income ceiling for {category} category"
        )

    ceiling = criteria.income_ceiling_by_category.get(category)
    if ceiling is None:
        ceiling = criteria.income_ceiling_general

    if ceiling is None and (criteria.income_ceiling_rural or criteria.income_ceiling_urban):
        ceiling = (
            criteria.income_ceiling_rural
            if student.residence_area == "rural"
            else criteria.income_ceiling_urban
        )

    if ceiling is None:
        return CriterionCheck(criterion="Family income", matched=True, reason="No income criteria specified")

    matched = student.family_income <= ceiling
    reason = (
        f"Family income ₹{student.family_income:,.0f} is within the ₹{ceiling:,.0f} limit"
        if matched
        else f"Family income ₹{student.family_income:,.0f} exceeds the ₹{ceiling:,.0f} limit"
    )
    return CriterionCheck(criterion="Family income", matched=matched, reason=reason)


def _check_education_level(student: StudentProfile, criteria: StructuredCriteria) -> CriterionCheck:
    if criteria.min_class is None and not criteria.education_keywords:
        return CriterionCheck(
            criterion="Education level", matched=True, reason="No education-level restriction found"
        )

    class_range = EDUCATION_LEVEL_TO_CLASS_RANGE.get(student.education_level)
    if class_range and criteria.min_class is not None and criteria.max_class is not None:
        matched = criteria.min_class <= class_range[1] and criteria.max_class >= class_range[0]
        if matched:
            return CriterionCheck(
                criterion="Education level",
                matched=True,
                reason=f"{student.education_level} falls within the scheme's Class {criteria.min_class}–{criteria.max_class} range",
            )

    student_keywords = EDUCATION_LEVEL_KEYWORDS.get(student.education_level, set())
    overlap = student_keywords & set(criteria.education_keywords)
    matched = bool(overlap)
    reason = (
        f"{student.education_level} matches scheme's stated education level"
        if matched
        else f"{student.education_level} does not match the scheme's target education level"
    )
    return CriterionCheck(criterion="Education level", matched=matched, reason=reason)


def _check_academic_percentage(student: StudentProfile, criteria: StructuredCriteria) -> CriterionCheck:
    if criteria.min_percentage_general is None:
        return CriterionCheck(
            criterion="Academic score", matched=True, reason="No minimum academic score specified"
        )

    percentage = student.effective_percentage()
    if percentage is None:
        return CriterionCheck(
            criterion="Academic score",
            matched=False,
            reason="No academic score provided to check against the requirement",
        )

    threshold = (
        criteria.min_percentage_sc_st
        if student.category in ("SC", "ST") and criteria.min_percentage_sc_st is not None
        else criteria.min_percentage_general
    )
    matched = percentage >= threshold
    reason = (
        f"{percentage:.1f}% meets the {threshold:.0f}% minimum requirement"
        if matched
        else f"{percentage:.1f}% is below the {threshold:.0f}% minimum requirement"
    )
    return CriterionCheck(criterion="Academic score", matched=matched, reason=reason)


def _check_parent_status(
    student: StudentProfile, criteria: StructuredCriteria
) -> CriterionCheck | None:
    if not criteria.requires_orphan_or_single_parent:
        return None
    matched = student.parent_status in ("orphan", "single_parent")
    reason = (
        "Scheme targets orphaned/single-parent children and student qualifies"
        if matched
        else "Scheme is restricted to orphaned or single-parent children"
    )
    return CriterionCheck(criterion="Parent status", matched=matched, reason=reason)


def _check_gender(
    student: StudentProfile, criteria: StructuredCriteria
) -> CriterionCheck | None:
    """Only adds a check if the scheme restricts to a specific gender."""
    if criteria.gender_restriction is None:
        return None  # Open to all — not a scored criterion
    matched = student.gender == criteria.gender_restriction
    reason = (
        f"Scheme is open to {criteria.gender_restriction} applicants and you qualify"
        if matched
        else f"Scheme is restricted to {criteria.gender_restriction} applicants"
    )
    return CriterionCheck(criterion="Gender", matched=matched, reason=reason)


def _check_age(
    student: StudentProfile, criteria: StructuredCriteria
) -> CriterionCheck | None:
    """Only adds a check when a scheme specifies an age range or limit."""
    if criteria.min_age is None and criteria.max_age is None:
        return None
    age = student.age
    if criteria.min_age is not None and criteria.max_age is not None:
        matched = criteria.min_age <= age <= criteria.max_age
        reason = (
            f"Age {age} is within the {criteria.min_age}–{criteria.max_age} year range"
            if matched
            else f"Age {age} is outside the required {criteria.min_age}–{criteria.max_age} year range"
        )
    elif criteria.max_age is not None:
        matched = age <= criteria.max_age
        reason = (
            f"Age {age} is within the under-{criteria.max_age} limit"
            if matched
            else f"Age {age} exceeds the {criteria.max_age}-year maximum"
        )
    else:
        matched = age >= criteria.min_age  # type: ignore[operator]
        reason = (
            f"Age {age} meets the minimum age of {criteria.min_age}"
            if matched
            else f"Age {age} is below the required minimum of {criteria.min_age}"
        )
    return CriterionCheck(criterion="Age", matched=matched, reason=reason)


def _check_disability(
    student: StudentProfile, criteria: StructuredCriteria
) -> CriterionCheck | None:
    """Only adds a check when a scheme explicitly requires a disability."""
    if not criteria.requires_disability:
        return None
    matched = student.disability
    reason = (
        "Scheme is for persons with disability and you have indicated a disability"
        if matched
        else "Scheme requires the applicant to have a registered disability"
    )
    return CriterionCheck(criterion="Disability", matched=matched, reason=reason)


# ── Student summary for embedding ─────────────────────────────────────────────

def _student_summary_text(student: StudentProfile) -> str:
    disability_clause = ", has a disability" if student.disability else ""
    religion = getattr(student, "religion", None)
    institution = getattr(student, "institution_type", None)
    religion_clause = f", {religion} community" if religion and religion not in ("prefer_not_to_say", "other") else ""
    institution_clause = f", studying at a {institution} institution" if institution else ""
    return (
        f"{student.age}-year-old {student.gender} student from {student.state} "
        f"({student.residence_area} area), {student.category} category{religion_clause}, "
        f"studying {student.education_level}{institution_clause}, "
        f"annual family income around ₹{student.family_income:,.0f}, "
        f"parent status: {student.parent_status.replace('_', ' ')}{disability_clause}."
    )


# ── Criteria richness (drives adaptive weight) ───────────────────────────────

def _criteria_richness(criteria: StructuredCriteria) -> int:
    """Count how many meaningful criteria fields were successfully extracted.

    Used to calibrate the adaptive scoring weight: high richness → trust the
    criteria score more; low richness → lean on the semantic embedding more.
    Max possible value is 10.
    """
    richness = 0
    if criteria.income_ceiling_general is not None:
        richness += 1
    if criteria.income_ceiling_by_category:
        richness += 1
    if criteria.no_income_limit_categories:
        richness += 1
    if criteria.min_class is not None:
        richness += 1
    if criteria.min_percentage_general is not None:
        richness += 1
    if criteria.eligible_categories:
        richness += 1
    if criteria.gender_restriction is not None:
        richness += 1
    if criteria.min_age is not None or criteria.max_age is not None:
        richness += 1
    if criteria.requires_disability:
        richness += 1
    if criteria.requires_orphan_or_single_parent:
        richness += 1
    return richness


# ── Main matching function ─────────────────────────────────────────────────────

def match_student(
    student: StudentProfile, schemes: list[dict], top_k: int | None = None
) -> list[MatchResult]:
    criteria_by_id = extract_all(schemes)

    student_text = _student_summary_text(student)
    scheme_texts = [s["ai_metadata"]["searchable_text"] for s in schemes]
    embeddings = embed_texts([student_text] + scheme_texts)
    student_vec, scheme_vecs = embeddings[0], embeddings[1:]

    results: list[MatchResult] = []
    for scheme, scheme_vec in zip(schemes, scheme_vecs):
        criteria = criteria_by_id[scheme["scheme_id"]]

        # Core mandatory checks (always included)
        checks = [
            _check_state(student, criteria),
            _check_category(student, criteria),
            _check_income(student, criteria),
            _check_education_level(student, criteria),
            _check_academic_percentage(student, criteria),
        ]

        # Optional checks — only added when the scheme actually constrains that field
        for optional_fn in (
            _check_parent_status,
            _check_gender,
            _check_age,
            _check_disability,
        ):
            result = optional_fn(student, criteria)
            if result is not None:
                checks.append(result)

        criteria_score = sum(1 for c in checks if c.matched) / len(checks)

        sim = cosine_similarity(student_vec, scheme_vec)
        semantic_score = max(0.0, min(1.0, (sim + 1) / 2))

        # Adaptive weights: richer criteria extraction → trust criteria more.
        # richness in [0, 10] → criteria_weight in [0.40, 0.65]
        richness = _criteria_richness(criteria)
        criteria_weight = round(0.40 + (richness / 10) * 0.25, 4)
        semantic_weight = round(1.0 - criteria_weight, 4)
        overall = round((criteria_weight * criteria_score + semantic_weight * semantic_score) * 100, 1)

        results.append(
            MatchResult(
                scheme_id=scheme["scheme_id"],
                scheme_name=scheme["scheme_name"],
                department=scheme.get("department"),
                overall_score=overall,
                semantic_score=round(semantic_score * 100, 1),
                criteria_score=round(criteria_score * 100, 1),
                criteria_breakdown=checks,
                required_documents=scheme.get("required_documents", []),
                official_website=scheme.get("official_website"),
                application_portal=scheme.get("application_portal"),
            )
        )

    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results[:top_k] if top_k else results
