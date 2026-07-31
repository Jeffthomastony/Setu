"""Retrieval + template-based question answering over the scheme dataset.

Deliberately NOT a free-generation chatbot: a question is embedded and
matched against the same scheme embeddings used for /search and /match,
the intent of the question is classified with keyword rules, and the
answer is filled in from the matched scheme's structured fields. This
keeps every answer traceable to a specific dataset field -- it cannot
invent facts about a scheme, and it declines to answer when nothing
matches confidently.
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.matching.embedder import cosine_similarity, embed_texts

# Word-vector average-pooled similarity has a "noise floor" of roughly
# 60-75% for almost any question against almost any scheme, since generic
# words dominate the pooled vector. A low threshold can't tell a real match
# from noise, so genuine matches are expected to clear this via the
# keyword-hit boost below; this floor mainly rejects fully off-topic
# questions with no distinctive terms.
MIN_CONFIDENCE = 78.0
KEYWORD_BOOST_SCORE = 95.0

GENERIC_WORDS = {
    "scholarship", "scholarships", "scheme", "schemes", "for", "the", "and", "of", "in",
    "students", "student", "education", "welfare", "merit", "state", "central", "government",
    "india", "development", "department", "post", "matric", "fee", "means", "cum", "national",
    "class", "college", "university", "social", "justice", "security", "mission", "with",
}


def _distinctive_tokens(scheme: dict) -> set[str]:
    words = re.findall(r"[A-Za-z]+", scheme["scheme_name"])
    for kw in scheme.get("ai_metadata", {}).get("keywords", []):
        words += re.findall(r"[A-Za-z]+", kw)
    return {w.lower() for w in words if len(w) >= 4 and w.lower() not in GENERIC_WORDS}


def _keyword_hit(question_lower: str, scheme: dict) -> bool:
    return any(
        re.search(r"\b" + re.escape(token) + r"\b", question_lower)
        for token in _distinctive_tokens(scheme)
    )

INTENT_KEYWORDS = {
    "documents": ["document", "documents", "papers", "certificate", "certificates", "proof"],
    "deadline": ["deadline", "last date", "due date", "when", "close", "closing"],
    "income": ["income", "salary", "earn", "earning", "family income"],
    "benefits": ["benefit", "benefits", "amount", "money", "stipend", "allowance", "scholarship amount", "how much"],
    "application_process": ["how to apply", "apply", "process", "steps", "registration", "register", "portal"],
    "eligibility": ["eligib", "who can apply", "qualify", "qualif", "criteria", "requirement"],
}

# Order matters: more specific intents are checked before the broad
# "eligibility" catch-all, since e.g. an income question also mentions
# "eligible" sometimes.
INTENT_ORDER = ["documents", "deadline", "income", "benefits", "application_process", "eligibility"]


def classify_intent(question: str) -> str:
    lower = question.lower()
    for intent in INTENT_ORDER:
        if any(kw in lower for kw in INTENT_KEYWORDS[intent]):
            return intent
    return "general"


@dataclass
class AnswerResult:
    answer: str
    scheme_id: Optional[str]
    scheme_name: Optional[str]
    matched_intent: str
    confidence: float
    source_fields: list[str]


def _find_best_scheme(question: str, schemes: list[dict]) -> tuple[Optional[dict], float]:
    if not schemes:
        return None, 0.0
    texts = [f"{s['scheme_name']}. {s['ai_metadata']['searchable_text']}" for s in schemes]
    embeddings = embed_texts([question] + texts)
    question_vec, scheme_vecs = embeddings[0], embeddings[1:]
    question_lower = question.lower()

    best_scheme, best_score = None, -1.0
    for scheme, vec in zip(schemes, scheme_vecs):
        sim = cosine_similarity(question_vec, vec)
        score = max(0.0, min(1.0, (sim + 1) / 2)) * 100

        if _keyword_hit(question_lower, scheme):
            score = max(score, KEYWORD_BOOST_SCORE)

        if score > best_score:
            best_scheme, best_score = scheme, score
    return best_scheme, best_score


def _format_eligibility(scheme: dict) -> tuple[str, list[str]]:
    elig = scheme.get("eligibility", {})
    parts, fields = [], []
    if elig.get("education_level"):
        parts.append(f"available for {elig['education_level']}")
        fields.append("eligibility.education_level")
    if elig.get("caste_category"):
        parts.append(f"open to {', '.join(elig['caste_category'])} category students")
        fields.append("eligibility.caste_category")
    if elig.get("income_limit"):
        parts.append(elig["income_limit"])
        fields.append("eligibility.income_limit")
    if elig.get("domicile"):
        parts.append(elig["domicile"])
        fields.append("eligibility.domicile")
    if elig.get("academic_percentage"):
        parts.append(elig["academic_percentage"])
        fields.append("eligibility.academic_percentage")
    text = "; ".join(parts) if parts else "No specific eligibility restrictions are listed for this scheme."
    return text, fields


def _format_income(scheme: dict) -> tuple[str, list[str]]:
    income = scheme.get("eligibility", {}).get("income_limit")
    if income:
        return income, ["eligibility.income_limit"]
    return "No income criteria is specified for this scheme in our data.", []


def _format_documents(scheme: dict) -> tuple[str, list[str]]:
    docs = scheme.get("required_documents") or []
    if docs:
        return "You'll typically need: " + ", ".join(docs) + ".", ["required_documents"]
    return "No specific document list is available for this scheme in our data.", []


def _format_deadline(scheme: dict) -> tuple[str, list[str]]:
    start = scheme.get("application_start_date")
    end = scheme.get("application_end_date")
    if start or end:
        return (
            f"Applications run from {start or 'an unspecified start date'} to {end or 'an unspecified end date'}.",
            ["application_start_date", "application_end_date"],
        )
    return (
        "No fixed deadline is published in our data for this scheme — check the official website for the "
        "current application window.",
        [],
    )


def _format_benefits(scheme: dict) -> tuple[str, list[str]]:
    benefits = scheme.get("benefits", {})
    parts, fields = [], []
    for key, label in [
        ("tuition_fee_support", "tuition fee support"),
        ("hostel_fee_support", "hostel fee support"),
        ("maintenance_allowance", "maintenance allowance"),
        ("book_allowance", "book allowance"),
        ("laptop_or_device_support", "laptop/device support"),
        ("travel_allowance", "travel allowance"),
    ]:
        if benefits.get(key):
            parts.append(f"{label}: {benefits[key]}")
            fields.append(f"benefits.{key}")
    other = benefits.get("other_benefits") or []
    if other:
        parts.append("other benefits: " + ", ".join(other))
        fields.append("benefits.other_benefits")
    text = ". ".join(parts) if parts else "No specific monetary benefits are listed for this scheme in our data."
    return text, fields


def _format_application_process(scheme: dict) -> tuple[str, list[str]]:
    application = scheme.get("application", {})
    steps = application.get("application_steps") or []
    if steps:
        return "Steps: " + " -> ".join(steps), ["application.application_steps"]
    mode = application.get("application_mode")
    if mode:
        return f"Application mode: {mode}.", ["application.application_mode"]
    return "No application process details are available for this scheme in our data.", []


def _format_general(scheme: dict) -> tuple[str, list[str]]:
    return scheme.get("description", "No description available."), ["description"]


ANSWER_FORMATTERS = {
    "eligibility": _format_eligibility,
    "income": _format_income,
    "documents": _format_documents,
    "deadline": _format_deadline,
    "benefits": _format_benefits,
    "application_process": _format_application_process,
    "general": _format_general,
}


def answer_question(question: str, schemes: list[dict]) -> AnswerResult:
    question = question.strip()
    if not question:
        return AnswerResult(
            answer="Please type a question about a scheme.",
            scheme_id=None,
            scheme_name=None,
            matched_intent="none",
            confidence=0.0,
            source_fields=[],
        )

    scheme, confidence = _find_best_scheme(question, schemes)

    if scheme is None or confidence < MIN_CONFIDENCE:
        return AnswerResult(
            answer=(
                "I couldn't confidently match your question to a specific scheme in our database. "
                "Try rephrasing with a scheme name or keyword, or use Search to browse all schemes."
            ),
            scheme_id=None,
            scheme_name=None,
            matched_intent="none",
            confidence=round(confidence, 1),
            source_fields=[],
        )

    intent = classify_intent(question)
    body, fields = ANSWER_FORMATTERS[intent](scheme)
    answer = f"For {scheme['scheme_name']}: {body}"

    return AnswerResult(
        answer=answer,
        scheme_id=scheme["scheme_id"],
        scheme_name=scheme["scheme_name"],
        matched_intent=intent,
        confidence=round(confidence, 1),
        source_fields=fields,
    )
