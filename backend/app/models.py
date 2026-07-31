from typing import Literal, Optional

from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    age: int = Field(..., ge=0, le=100)
    family_income: float = Field(..., ge=0, description="Annual family income in INR")
    category: Literal["General", "OBC", "SC", "ST", "OEC"]
    state: str
    residence_area: Literal["rural", "urban"]
    education_level: Literal[
        "Class 1-5",
        "Class 6-7",
        "Class 8",
        "Class 9-10",
        "Class 11-12",
        "ITI",
        "Polytechnic/Diploma",
        "Undergraduate",
        "Postgraduate",
        "Professional",
        "Doctoral",
    ]
    academic_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Most recent exam percentage"
    )
    cgpa: Optional[float] = Field(
        None, ge=0, le=10, description="Most recent CGPA on a 10-point scale"
    )
    parent_status: Literal["both_parents", "single_parent", "orphan"]
    gender: Literal["male", "female", "other"]
    disability: bool = False
    # Optional enrichment fields — improve semantic matching accuracy
    religion: Optional[str] = None
    institution_type: Optional[str] = None

    def effective_percentage(self) -> Optional[float]:
        """Normalize CGPA to a percentage if percentage wasn't given directly."""
        if self.academic_percentage is not None:
            return self.academic_percentage
        if self.cgpa is not None:
            return round(self.cgpa * 9.5, 2)
        return None


class SeniorCitizenProfile(BaseModel):
    age: int = Field(..., ge=60, le=120)
    family_income: float = Field(..., ge=0, description="Annual family income in INR")
    category: Literal["General", "OBC", "SC", "ST", "OEC"]
    state: str
    residence_area: Literal["rural", "urban"]
    gender: Literal["male", "female", "other"]
    disability: bool = False
    # Optional enrichment fields — improve senior citizen scheme matching
    marital_status: Optional[str] = None       # 'married', 'widowed', 'single', 'divorced_abandoned'
    ration_card_type: Optional[str] = None     # 'bpl', 'aay_antyodaya', 'apl', 'priority_household', 'none'
    living_status: Optional[str] = None        # 'with_family', 'living_alone', 'old_age_home'



class CriterionCheck(BaseModel):
    criterion: str
    matched: bool
    reason: str


class MatchResult(BaseModel):
    scheme_id: str
    scheme_name: str
    department: Optional[str] = None
    overall_score: float
    semantic_score: float
    criteria_score: float
    criteria_breakdown: list[CriterionCheck]
    required_documents: list[str]
    official_website: Optional[str] = None
    application_portal: Optional[str] = None
    # Extra fields forwarded from scheme JSON for richer UI display
    benefits: dict = Field(default_factory=dict)
    scheme_type: Optional[str] = None
    state: Optional[str] = None
    description: Optional[str] = None


class SchemeSearchResult(BaseModel):
    scheme_id: str
    scheme_name: str
    department: Optional[str] = None
    state: str
    description: str
    relevance_score: float
    required_documents: list[str]
    official_website: Optional[str] = None
    application_portal: Optional[str] = None
