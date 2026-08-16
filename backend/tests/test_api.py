"""API tests for the FastAPI app. Uses the real trained model artifacts
(loaded once at import) but a throwaway data file per test."""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import store


@pytest.fixture(autouse=True)
def isolated_data_file(tmp_path, monkeypatch):
    fake_file = tmp_path / "candidates.json"
    monkeypatch.setattr(store, "DATA_FILE", fake_file)
    yield fake_file


@pytest.fixture()
def client():
    import main
    return TestClient(main.app)


def _minimal_pdf_bytes(text="Python developer with 5 years of experience. Bachelor's degree. Certified Scrum Master."):
    """Build a tiny valid PDF with extractable text, without needing a fixture file."""
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 700, text)
    c.save()
    buf.seek(0)
    return buf.read()


def test_get_categories_returns_known_categories(client):
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "INFORMATION-TECHNOLOGY" in data["categories"]


def test_analyze_resume_rejects_non_pdf(client):
    res = client.post(
        "/api/analyze-resume",
        data={"category": "INFORMATION-TECHNOLOGY"},
        files={"file": ("resume.txt", b"not a pdf", "text/plain")},
    )
    assert res.status_code == 400


def test_analyze_resume_accepts_pdf_and_returns_prediction(client):
    pdf_bytes = _minimal_pdf_bytes()
    res = client.post(
        "/api/analyze-resume",
        data={"category": "INFORMATION-TECHNOLOGY"},
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "resume.pdf"
    assert body["category"] == "INFORMATION-TECHNOLOGY"
    assert 0 <= body["prediction"]["fit_score"] <= 100
    assert body["prediction"]["fit_category"] in ("Strong Fit", "Moderate Fit", "Weak Fit")


def test_candidates_list_empty_by_default(client):
    res = client.get("/api/candidates")
    assert res.status_code == 200
    assert res.json() == {"candidates": []}


def test_decision_flow_approve(client):
    pdf_bytes = _minimal_pdf_bytes()
    analyze_res = client.post(
        "/api/analyze-resume",
        data={"category": "HR"},
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    candidate_id = analyze_res.json()["id"]

    decision_res = client.post("/api/decision", json={
        "candidate_id": candidate_id,
        "decision": "approve",
        "reason": "Strong background",
    })
    assert decision_res.status_code == 200
    assert decision_res.json()["decision"] == "approve"


def test_decision_rejects_invalid_decision_value(client):
    res = client.post("/api/decision", json={
        "candidate_id": "whatever",
        "decision": "maybe",
        "reason": "unsure",
    })
    assert res.status_code == 400


def test_decision_unknown_candidate_returns_404(client):
    res = client.post("/api/decision", json={
        "candidate_id": "does-not-exist",
        "decision": "approve",
        "reason": "reason",
    })
    assert res.status_code == 404


def test_report_download_returns_pdf(client):
    res = client.get("/api/report")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_frontend_index_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "HR Resume Screening" in res.text
