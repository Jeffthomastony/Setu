"""NLP-based extraction of structured eligibility criteria from the free-text
eligibility fields found in scheme records (income_limit, academic_percentage,
education_level, other_conditions).

Even though the input JSON is partially structured, several fields are still
human-readable prose (e.g. "No income limit for SC, ST and OEC students;
annual family income below Rs 1,00,000 for OBC students"). This module turns
that prose into clean, comparable values the matching engine can use.
"""

import re
import threading
from dataclasses import dataclass, field
from typing import Optional

import spacy

_nlp = None
_lock = threading.Lock()

CATEGORY_ALIASES = {
    "sc": "SC",
    "st": "ST",
    "obc": "OBC",
    "oec": "OEC",
    "general": "General",
}

CURRENCY_RE = re.compile(r"[₹Rs.]*\s?([\d,]{3,}(?:\.\d+)?)")
PERCENT_RE = re.compile(r"(\d{1,3})\s?%")
CLASS_RE = re.compile(r"class\s*(\d{1,2})", re.IGNORECASE)
AGE_RANGE_RE = re.compile(r"(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*years?", re.IGNORECASE)
AGE_MAX_RE = re.compile(r"(?:below|under|up to|upto)\s*(\d{1,2})\s*years?", re.IGNORECASE)
# Qualifier-before-number phrasing: "above 60 years", "at least 60 years"
AGE_MIN_PREFIX_RE = re.compile(r"(?:above|atleast|at least|minimum)\s*(\d{1,2})\s*years?", re.IGNORECASE)
# Number-before-qualifier phrasing: "60 years and above", "70 years of age or above"
AGE_MIN_POSTFIX_RE = re.compile(
    r"(\d{1,2})\s*years?\s*(?:of age\s*)?(?:and above|or above|and over|or older|and older|\+)",
    re.IGNORECASE,
)

# Presence of any of these alongside a numeric class mention means the range
# actually extends into higher education (e.g. "Class 1 to Degree/
# Professional courses"), not just the highest digit the regex captured.
HIGHER_ED_KEYWORDS = (
    "degree",
    "graduation",
    "undergraduate",
    "postgraduate",
    "professional",
    "diploma",
    "polytechnic",
    "iti",
    "doctoral",
)
HIGHER_ED_CLASS_CEILING = 20


def get_nlp():
    """Lazily load spaCy in a thread-safe manner, falling back to a blank
    pipeline + sentencizer if the pretrained English model isn't installed."""
    global _nlp
    if _nlp is not None:
        return _nlp
    with _lock:
        if _nlp is not None:
            return _nlp
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = spacy.blank("en")
            _nlp.add_pipe("sentencizer")
    return _nlp


def _parse_amount(text: str) -> Optional[float]:
    m = CURRENCY_RE.search(text)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def _extract_gender_restriction(gender_field: Optional[str]) -> Optional[str]:
    """Return 'female', 'male', or None (open to all) from the gender field."""
    if not gender_field:
        return None
    lower = gender_field.lower().strip()
    if lower in ("all", "any", "both", "no restriction", ""):
        return None
    if "female" in lower or "girl" in lower or "women" in lower or "woman" in lower:
        return "female"
    if "male" in lower or "boy" in lower or "men" in lower or "man" in lower:
        return "male"
    return None


@dataclass
class StructuredCriteria:
    income_ceiling_general: Optional[float] = None
    income_ceiling_by_category: dict = field(default_factory=dict)
    income_ceiling_rural: Optional[float] = None
    income_ceiling_urban: Optional[float] = None
    no_income_limit_categories: list = field(default_factory=list)
    min_class: Optional[int] = None
    max_class: Optional[int] = None
    education_keywords: list = field(default_factory=list)
    min_percentage_general: Optional[float] = None
    min_percentage_sc_st: Optional[float] = None
    eligible_categories: list = field(default_factory=list)
    requires_orphan_or_single_parent: bool = False
    state: Optional[str] = None
    # New fields
    gender_restriction: Optional[str] = None   # 'female', 'male', or None=open
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    requires_disability: bool = False
    requires_widowed: bool = False
    requires_bpl: bool = False


def extract_criteria(scheme: dict) -> StructuredCriteria:
    elig = scheme.get("eligibility", {})
    nlp = get_nlp()

    criteria = StructuredCriteria()
    criteria.state = scheme.get("state")
    criteria.eligible_categories = [c.upper() for c in (elig.get("caste_category") or [])]

    # --- Income parsing: split into sentences, look for a $-amount near a
    # category mention, or a "no limit" phrase, in each sentence. ---
    income_text = elig.get("income_limit") or ""
    doc = nlp(income_text)
    sentences = list(doc.sents) if income_text else []

    no_limit_cats = []
    cat_ceiling = {}
    general_ceiling = None

    for sent in sentences:
        lower = sent.text.lower()
        amount = _parse_amount(sent.text)
        mentioned_cats = [full for alias, full in CATEGORY_ALIASES.items() if alias in lower]

        if "no income limit" in lower or "no limit" in lower:
            no_limit_cats.extend(mentioned_cats)
            continue

        if amount is not None:
            if mentioned_cats:
                for cat in mentioned_cats:
                    cat_ceiling[cat] = amount
            else:
                general_ceiling = amount

        if "rural" in lower and amount is not None:
            criteria.income_ceiling_rural = amount
        if "urban" in lower and amount is not None:
            criteria.income_ceiling_urban = amount

    criteria.income_ceiling_by_category = cat_ceiling
    criteria.income_ceiling_general = general_ceiling
    criteria.no_income_limit_categories = no_limit_cats

    # --- Percentage parsing ---
    pct_text = elig.get("academic_percentage") or ""
    percentages = [float(m.group(1)) for m in PERCENT_RE.finditer(pct_text)]
    if percentages:
        criteria.min_percentage_general = percentages[0]
        criteria.min_percentage_sc_st = percentages[-1] if len(percentages) > 1 else percentages[0]

    # --- Class range parsing (drives which school/course levels qualify) ---
    edu_text = elig.get("education_level") or ""
    classes = [int(m.group(1)) for m in CLASS_RE.finditer(edu_text)]
    if classes:
        criteria.min_class = min(classes)
        if any(kw in edu_text.lower() for kw in HIGHER_ED_KEYWORDS):
            criteria.max_class = HIGHER_ED_CLASS_CEILING
        else:
            criteria.max_class = max(classes)

    criteria.education_keywords = [
        tok.lemma_.lower() for tok in nlp(edu_text) if tok.is_alpha and not tok.is_stop
    ]

    # --- Orphan / single-parent condition, detected from prose in
    # other_conditions rather than a dedicated field ---
    other_conditions_text = " ".join(elig.get("other_conditions") or [])
    if re.search(r"lost (one or both|a|one)?\s?parent", other_conditions_text, re.IGNORECASE):
        criteria.requires_orphan_or_single_parent = True

    # --- Widowhood requirement, detected from prose in other_conditions
    # (e.g. widow pension schemes) ---
    if re.search(r"\bwidow", other_conditions_text, re.IGNORECASE):
        criteria.requires_widowed = True

    # --- BPL / Below Poverty Line requirement, detected from the income
    # eligibility text (many pension schemes gate on BPL status rather than,
    # or in addition to, a numeric income ceiling) ---
    if re.search(r"\bBPL\b|below poverty line", income_text, re.IGNORECASE):
        criteria.requires_bpl = True

    # --- Gender restriction ---
    criteria.gender_restriction = _extract_gender_restriction(elig.get("gender"))

    # --- Age range ---
    age_text = elig.get("age") or ""
    if not age_text and elig.get("other_conditions"):
        age_text = " ".join(elig.get("other_conditions"))

    if age_text:
        range_match = AGE_RANGE_RE.search(age_text)
        if range_match:
            criteria.min_age = int(range_match.group(1))
            criteria.max_age = int(range_match.group(2))
        else:
            max_match = AGE_MAX_RE.search(age_text)
            if max_match:
                criteria.max_age = int(max_match.group(1))
            min_match = AGE_MIN_PREFIX_RE.search(age_text) or AGE_MIN_POSTFIX_RE.search(age_text)
            if min_match:
                criteria.min_age = int(min_match.group(1))

    # --- Disability-specific schemes ---
    disability_field = elig.get("disability") or ""
    if disability_field and str(disability_field).strip().lower() not in ("null", "none", ""):
        disability_lower = str(disability_field).lower()
        if any(kw in disability_lower for kw in ("required", "only", "must", "persons with")):
            criteria.requires_disability = True

    return criteria


def extract_all(schemes: list[dict]) -> dict[str, StructuredCriteria]:
    return {scheme["scheme_id"]: extract_criteria(scheme) for scheme in schemes}
