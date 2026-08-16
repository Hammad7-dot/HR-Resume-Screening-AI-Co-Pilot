"""Unit tests for the JSON-file candidate/decision store (the HITL audit trail)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import store


@pytest.fixture(autouse=True)
def isolated_data_file(tmp_path, monkeypatch):
    """Point the store at a throwaway JSON file so tests never touch real data."""
    fake_file = tmp_path / "candidates.json"
    monkeypatch.setattr(store, "DATA_FILE", fake_file)
    yield fake_file


def sample_prediction():
    return {
        "fit_score": 72.5,
        "fit_category": "Strong Fit",
        "confidence": 88.0,
        "top_features": [{"feature": "skills_count", "impact": 1.2}],
        "narration": "Scored well.",
        "raw_features": {
            "years_experience": 4,
            "education_level": 3,
            "certifications_count": 1,
            "skills_found": ["python", "sql"],
        },
    }


def test_add_candidate_creates_record_with_expected_fields():
    record = store.add_candidate("resume.pdf", "INFORMATION-TECHNOLOGY", sample_prediction())
    assert record["filename"] == "resume.pdf"
    assert record["category"] == "INFORMATION-TECHNOLOGY"
    assert record["decision"] is None
    assert record["id"]
    assert record["uploaded_at"]


def test_list_candidates_returns_all_added():
    store.add_candidate("a.pdf", "HR", sample_prediction())
    store.add_candidate("b.pdf", "SALES", sample_prediction())
    candidates = store.list_candidates()
    assert len(candidates) == 2
    filenames = {c["filename"] for c in candidates}
    assert filenames == {"a.pdf", "b.pdf"}


def test_set_decision_updates_record():
    record = store.add_candidate("resume.pdf", "HR", sample_prediction())
    updated = store.set_decision(record["id"], "approve", "Great fit", None)
    assert updated["decision"] == "approve"
    assert updated["decision_reason"] == "Great fit"
    assert updated["decided_at"] is not None


def test_set_decision_unknown_candidate_raises_keyerror():
    with pytest.raises(KeyError):
        store.set_decision("does-not-exist", "approve", "reason", None)


def test_approved_candidates_filters_by_decision():
    a = store.add_candidate("a.pdf", "HR", sample_prediction())
    b = store.add_candidate("b.pdf", "HR", sample_prediction())
    store.set_decision(a["id"], "approve", "good", None)
    store.set_decision(b["id"], "reject", "not a fit", None)
    approved = store.approved_candidates()
    assert len(approved) == 1
    assert approved[0]["id"] == a["id"]


def test_get_candidate_returns_none_for_missing():
    assert store.get_candidate("nope") is None
