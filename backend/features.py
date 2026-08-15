"""
Feature engineering — must stay byte-for-byte identical in logic to the
Colab data-prep notebook that produced processed_features.csv, or live
predictions will silently drift from what the ANN was trained on.
"""
import pickle
import re
from pathlib import Path

# ---- Skill bank loaded from the JD-derived pickle exported by the full-train
# notebook (skill_bank.pkl). Falls back to a small hardcoded bank only if that
# artifact is missing, so the module still imports cleanly in a fresh checkout. ----
_ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
_SKILL_BANK_PATH = _ARTIFACTS_DIR / "skill_bank.pkl"

if _SKILL_BANK_PATH.exists():
    with open(_SKILL_BANK_PATH, "rb") as f:
        _bank_data = pickle.load(f)
    SKILL_BANK = _bank_data["SKILL_BANK"]
    DEFAULT_SKILLS = _bank_data["DEFAULT_SKILLS"]
else:
    SKILL_BANK = {
        'INFORMATION-TECHNOLOGY': ['python', 'sql', 'java', 'cloud', 'aws', 'api', 'docker', 'linux', 'javascript'],
        'HR': ['recruiting', 'onboarding', 'employee relations', 'payroll', 'hris', 'talent acquisition',
               'performance management', 'benefits administration', 'compliance', 'conflict resolution'],
        'DESIGNER': ['photoshop', 'figma', 'illustrator', 'ui', 'ux', 'branding', 'typography'],
        'SALES': ['crm', 'negotiation', 'lead generation', 'salesforce', 'quota', 'pipeline'],
        'HEALTHCARE': ['patient care', 'clinical', 'hipaa', 'ehr', 'nursing', 'diagnosis',
                       'medical terminology', 'patient safety', 'care coordination', 'vital signs'],
        'TEACHER': ['curriculum', 'lesson planning', 'classroom management', 'assessment',
                    'differentiated instruction', 'iep', 'student engagement', 'parent communication'],
        'BUSINESS-DEVELOPMENT': ['partnerships', 'market research', 'strategy', 'stakeholder',
                                  'lead generation', 'business strategy', 'negotiation', 'growth strategy',
                                  'client acquisition'],
        'ACCOUNTANT': ['quickbooks', 'gaap', 'accounts payable', 'accounts receivable',
                       'reconciliation', 'general ledger', 'financial reporting', 'audit',
                       'tax preparation', 'sap', 'budgeting', 'forecasting', 'cpa',
                       'bookkeeping', 'payroll', 'variance analysis'],
        'FINANCE': ['financial modeling', 'valuation', 'forecasting', 'budgeting', 'excel',
                    'financial analysis', 'risk management', 'investment analysis', 'cfa',
                    'variance analysis', 'cash flow'],
        'BANKING': ['underwriting', 'kyc', 'aml', 'loan processing', 'credit analysis',
                    'compliance', 'teller', 'risk management', 'retail banking', 'wire transfers'],
    }
    DEFAULT_SKILLS = ['communication', 'teamwork', 'project management', 'leadership', 'excel']

# All 24 categories the model was trained on (order doesn't matter here,
# but the SET must match feature_names.pkl's cat_* columns).
KNOWN_CATEGORIES = [
    'ACCOUNTANT', 'ADVOCATE', 'AGRICULTURE', 'APPAREL', 'ARTS', 'AUTOMOBILE',
    'AVIATION', 'BANKING', 'BPO', 'BUSINESS-DEVELOPMENT', 'CHEF', 'CONSTRUCTION',
    'CONSULTANT', 'DESIGNER', 'DIGITAL-MEDIA', 'ENGINEERING', 'FINANCE', 'FITNESS',
    'HEALTHCARE', 'HR', 'INFORMATION-TECHNOLOGY', 'PUBLIC-RELATIONS', 'SALES', 'TEACHER',
]


def extract_years_experience(text: str) -> int:
    text = text.lower()
    matches = re.findall(r'(\d{1,2})\s*\+?\s*(?:years|yrs)\b', text)
    years = [int(m) for m in matches if int(m) < 50]
    return max(years) if years else 0


EDUCATION_LEVELS = {
    'phd': 5, 'doctorate': 5,
    'master': 4, 'm.s.': 4, 'mba': 4,
    'bachelor': 3, 'b.s.': 3, 'b.a.': 3,
    'associate': 2,
    'high school': 1,
}


def extract_education_level(text: str) -> int:
    text = text.lower()
    level = 0
    for kw, score in EDUCATION_LEVELS.items():
        if kw in text:
            level = max(level, score)
    return level


def extract_certifications_count(text: str) -> int:
    text = text.lower()
    return len(re.findall(r'certifi(?:ed|cation|cate)', text))


def extract_skills_found(text: str, category: str):
    text = text.lower()
    bank = SKILL_BANK.get(category, []) + DEFAULT_SKILLS
    return sorted({s for s in bank if s in text})


def extract_all_features(resume_text: str, category: str) -> dict:
    """Raw (unscaled, un-encoded) features for one resume — the tabular modality."""
    skills = extract_skills_found(resume_text, category)
    return {
        'years_experience': extract_years_experience(resume_text),
        'education_level': extract_education_level(resume_text),
        'certifications_count': extract_certifications_count(resume_text),
        'skills_count': len(skills),
        'skills_found': skills,
        'category': category,
    }


def to_model_row(features: dict, feature_names: list) -> list:
    """Build the exact ordered feature row the ANN expects, given feature_names.pkl."""
    row = []
    for name in feature_names:
        if name == 'years_experience':
            row.append(features['years_experience'])
        elif name == 'education_level':
            row.append(features['education_level'])
        elif name == 'certifications_count':
            row.append(features['certifications_count'])
        elif name == 'skills_count':
            row.append(features['skills_count'])
        elif name.startswith('cat_'):
            row.append(1 if name == f"cat_{features['category']}" else 0)
        else:
            row.append(0)
    return row
