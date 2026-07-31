"""Retrieval-grounded Q&A over a single scheme's structured data.

Given a free-text question about a specific scheme, this module:
1. Turns the scheme's structured fields (eligibility, benefits, application
   process, documents, etc.) into a set of short, self-contained fact
   sentences — the "knowledge base" for that scheme.
2. Ranks those facts against the question using the same semantic-embedding
   + keyword-overlap blend the search endpoint uses.
3. Returns the top-matching facts as the answer, so every answer is
   traceable back to a specific field in the scheme record — no free-form
   generation, no risk of the model inventing eligibility rules or dates.
"""

from app.matching.embedder import cosine_similarity, embed_texts

MIN_ANSWER_SCORE = 0.22
TOP_K_FACTS = 3

FALLBACK_ANSWER = (
    "This scheme's available data doesn't clearly answer that question. "
    "Try rephrasing, or check the official website/application portal for details."
)


def build_fact_sheet(scheme: dict) -> list[str]:
    """Flatten a scheme record into short natural-language fact sentences."""
    facts: list[str] = []
    name = scheme.get("scheme_name", "This scheme")

    if scheme.get("description"):
        facts.append(scheme["description"])

    dept = scheme.get("department")
    ministry = scheme.get("ministry")
    if dept:
        facts.append(f"{name} is administered by {dept}.")
    if ministry:
        facts.append(f"{name} falls under the {ministry}.")

    elig = scheme.get("eligibility") or {}
    if elig.get("caste_category"):
        facts.append(f"Eligible caste/category: {', '.join(elig['caste_category'])}.")
    if elig.get("income_limit"):
        facts.append(f"Income eligibility: {elig['income_limit']}.")
    if elig.get("academic_percentage"):
        facts.append(f"Academic requirement: {elig['academic_percentage']}.")
    if elig.get("education_level"):
        facts.append(f"Eligible education level: {elig['education_level']}.")
    if elig.get("gender"):
        facts.append(f"Gender eligibility: {elig['gender']}.")
    if elig.get("age"):
        facts.append(f"Age requirement: {elig['age']}.")
    if elig.get("disability"):
        facts.append(f"Disability requirement: {elig['disability']}.")
    if elig.get("domicile"):
        facts.append(f"Domicile/residency requirement: {elig['domicile']}.")
    if elig.get("institution_type"):
        facts.append(f"Eligible institution type: {elig['institution_type']}.")
    if elig.get("course_type"):
        facts.append(f"Eligible course type: {elig['course_type']}.")
    if elig.get("attendance_requirement"):
        facts.append(f"Attendance requirement: {elig['attendance_requirement']}.")
    if elig.get("year_of_study"):
        facts.append(f"Year of study covered: {elig['year_of_study']}.")
    for condition in elig.get("other_conditions") or []:
        facts.append(f"Additional condition: {condition}.")

    benefits = scheme.get("benefits") or {}
    benefit_labels = {
        "tuition_fee_support": "Tuition fee support",
        "maintenance_allowance": "Maintenance allowance",
        "laptop_or_device_support": "Laptop/device support",
        "book_allowance": "Book allowance",
        "hostel_fee_support": "Hostel fee support",
        "travel_allowance": "Travel allowance",
    }
    for field_name, label in benefit_labels.items():
        value = benefits.get(field_name)
        if value:
            facts.append(f"{label}: {value}.")
    for extra in benefits.get("other_benefits") or []:
        facts.append(f"Other benefit: {extra}.")

    application = scheme.get("application") or {}
    if application.get("application_mode"):
        facts.append(f"How to apply: {application['application_mode']}.")
    if application.get("application_steps"):
        steps = application["application_steps"]
        numbered = "; ".join(f"{i + 1}) {step}" for i, step in enumerate(steps))
        facts.append(f"Application steps for {name}: {numbered}.")
    if application.get("processing_time"):
        facts.append(f"Processing time: {application['processing_time']}.")
    if application.get("renewal_required") is not None:
        facts.append(
            f"Renewal required each year: {'yes' if application['renewal_required'] else 'no'}."
        )
    if scheme.get("application_start_date"):
        facts.append(f"Application start date: {scheme['application_start_date']}.")
    if scheme.get("application_end_date"):
        facts.append(f"Application deadline: {scheme['application_end_date']}.")

    if scheme.get("required_documents"):
        facts.append(
            f"Documents required: {', '.join(scheme['required_documents'])}."
        )

    if scheme.get("official_website"):
        facts.append(f"Official website: {scheme['official_website']}.")
    if scheme.get("application_portal"):
        facts.append(f"Application portal: {scheme['application_portal']}.")

    return facts


def answer_question(scheme: dict, question: str) -> dict:
    """Answer a free-text question about a scheme, grounded in its fact sheet."""
    facts = build_fact_sheet(scheme)
    scheme_id = scheme.get("scheme_id")
    scheme_name = scheme.get("scheme_name")

    if not facts:
        return {
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "question": question,
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": 0.0,
        }

    try:
        embeddings = embed_texts([question] + facts)
        query_vec = embeddings[0]
        fact_vecs = embeddings[1:]
        semantic_scores = [float(cosine_similarity(query_vec, fv)) for fv in fact_vecs]
    except Exception:
        semantic_scores = [0.0] * len(facts)

    query_terms = [t for t in question.lower().split() if len(t) > 2]

    scored: list[tuple[float, str]] = []
    for fact, sem_score in zip(facts, semantic_scores):
        fact_lower = fact.lower()
        if query_terms:
            keyword_hits = sum(1 for term in query_terms if term in fact_lower)
            keyword_score = keyword_hits / len(query_terms)
        else:
            keyword_score = 0.0
        sem_norm = max(0.0, min(1.0, (sem_score + 1) / 2))
        combined = 0.5 * keyword_score + 0.5 * sem_norm
        scored.append((combined, fact))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [pair for pair in scored[:TOP_K_FACTS] if pair[0] >= MIN_ANSWER_SCORE]

    if not top:
        return {
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "question": question,
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": round(scored[0][0], 2) if scored else 0.0,
        }

    answer = " ".join(fact for _, fact in top)

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "question": question,
        "answer": answer,
        "sources": [fact for _, fact in top],
        "confidence": round(top[0][0], 2),
    }
