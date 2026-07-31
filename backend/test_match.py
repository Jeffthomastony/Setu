import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.models import StudentProfile, SeniorCitizenProfile
from app.matching.matcher import match_student, match_senior_citizen
from app.api.routes import load_schemes, load_senior_schemes

print("Testing Student Matching...")
std = StudentProfile(
    age=20, family_income=120000, category="OBC", state="Kerala",
    residence_area="rural", education_level="Undergraduate",
    parent_status="both_parents", gender="female"
)
std_res = match_student(std, load_schemes())
print(f"[OK] Student matches: {len(std_res)} found. Top match: {std_res[0].scheme_name} ({std_res[0].overall_score}%)")

print("\nTesting Senior Citizen Matching...")
sen = SeniorCitizenProfile(
    age=65, family_income=50000, category="General", state="Kerala",
    residence_area="rural", gender="female", disability=True
)
sen_res = match_senior_citizen(sen, load_senior_schemes())
print(f"[OK] Senior matches: {len(sen_res)} found. Top match: {sen_res[0].scheme_name} ({sen_res[0].overall_score}%)")

print("\nSUCCESS! Both pipelines executed cleanly with zero errors.")
