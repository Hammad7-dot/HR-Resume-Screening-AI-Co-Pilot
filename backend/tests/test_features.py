"""Unit tests for feature engineering — resume text -> tabular features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import features


def test_extract_years_experience_takes_max_under_50():
    text = "I have 5 years of experience and later gained 8+ years in the field."
    assert features.extract_years_experience(text) == 8


def test_extract_years_experience_ignores_unrealistic_values():
    # The \d{1,2} pattern only ever captures 1-2 digits, so 3-digit runs like
    # "120 years" get read as their trailing 2 digits ("20 years") rather than
    # rejected outright; extract_years_experience's >= 50 filter guards against
    # genuinely 2-digit unrealistic values instead.
    text = "This 99 years old institution..."
    assert features.extract_years_experience(text) == 0


def test_extract_years_experience_defaults_to_zero():
    assert features.extract_years_experience("No experience mentioned here.") == 0


def test_extract_education_level_picks_highest():
    text = "I hold a Bachelor's degree and later completed my Master's in Business."
    assert features.extract_education_level(text) == 4


def test_extract_education_level_defaults_to_zero():
    assert features.extract_education_level("Nothing relevant here.") == 0


def test_extract_certifications_count():
    text = "AWS Certified Solutions Architect. PMP certification. Certified Scrum Master."
    assert features.extract_certifications_count(text) == 3


def test_extract_skills_found_matches_category_bank():
    text = "Experienced with python, sql and docker in cloud environments."
    skills = features.extract_skills_found(text, "INFORMATION-TECHNOLOGY")
    assert "python" in skills
    assert "sql" in skills
    assert "docker" in skills


def test_extract_skills_found_unknown_category_uses_default_only():
    text = "Strong communication and teamwork skills, leadership experience."
    skills = features.extract_skills_found(text, "SOME-UNKNOWN-CATEGORY")
    assert set(skills).issubset(set(features.DEFAULT_SKILLS))
    assert len(skills) > 0


def test_extract_all_features_shape():
    text = "5 years of experience. Bachelor's degree. Certified in project management. Python, SQL."
    result = features.extract_all_features(text, "INFORMATION-TECHNOLOGY")
    assert set(result.keys()) == {
        "years_experience", "education_level", "certifications_count",
        "skills_count", "skills_found", "category",
    }
    assert result["category"] == "INFORMATION-TECHNOLOGY"
    assert result["skills_count"] == len(result["skills_found"])


def test_to_model_row_orders_by_feature_names():
    raw = {
        "years_experience": 3,
        "education_level": 2,
        "certifications_count": 1,
        "skills_count": 4,
        "category": "HR",
    }
    feature_names = ["years_experience", "cat_HR", "education_level", "cat_SALES", "skills_count", "certifications_count"]
    row = features.to_model_row(raw, feature_names)
    assert row == [3, 1, 2, 0, 4, 1]


def test_known_categories_is_nonempty_and_unique():
    assert len(features.KNOWN_CATEGORIES) == len(set(features.KNOWN_CATEGORIES))
    assert len(features.KNOWN_CATEGORIES) > 0
