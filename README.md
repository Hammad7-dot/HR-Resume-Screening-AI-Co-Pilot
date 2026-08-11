# HR Resume Screening — AI Co-Pilot

An AI-assisted resume screening web app that scores candidate fit against a job category with a trained neural network, explains every score with SHAP, and requires a recruiter to approve, reject, or modify each result before it counts as final — keeping a human in the loop at all times.

## Overview

Recruiters manually screening large volumes of resumes is slow, inconsistent, and prone to bias. This Co-Pilot parses resume PDFs, extracts structured features, scores fit with a trained ANN, and explains *why* using SHAP — while a recruiter stays in control of every final decision.

## Features

- **Multi-modal input** — resume PDFs (layout-aware parsing), resume text, and structured tabular features (years of experience, education level, certifications, skill count, category).
- **Predictive deep learning model** — a feed-forward ANN (PyTorch) produces the Fit Score (0–100); the LLM, if used, only narrates — it never predicts.
- **Explainable AI** — calibrated confidence score (MC-Dropout) and top SHAP features per prediction, shown in the UI and in the exported report.
- **Human-in-the-loop** — nothing is final until a recruiter clicks Approve, Reject, or Modify Score with a reason; every decision is logged with a timestamp for audit.
- **Downloadable report** — auto-generated PDF shortlist with Fit Scores, SHAP rationale, and the recruiter audit trail.

## Project structure

```
backend/
  main.py                 FastAPI app — REST API + serves the frontend
  model.py                Loads the trained ANN + scaler, calibrated MC-Dropout confidence, SHAP
  features.py             Resume -> tabular features, skill bank loaded from skill_bank.pkl
  reports.py               Generates the downloadable PDF shortlist report
  store.py                 JSON-file candidate + decision storage (the HITL audit trail)
  artifacts/                fit_score_ann.pt, scaler.pkl, feature_names.pkl, skill_bank.pkl,
                             confidence_calibration.pkl, feature_importance.csv, processed_features.csv
  requirements.txt
frontend/
  index.html / style.css / app.js    Recruiter dashboard (no build step needed)
docs/
  spec.md / decision.md / rules.md / block.md    Project spec, decisions, and rules
```

## Setup & run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** — frontend and API are served from the same process.

## Tech stack

- **Backend:** FastAPI, PyTorch, SHAP, scikit-learn, pandas, pdfplumber, ReportLab
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **Storage:** JSON-file candidate + decision store

## Known limitations

- `skills_count` dominates predictions — years of experience and education level move the score much less, by design of the synthetic training label (skill-overlap %).
- Skill-bank keyword coverage is currently thin for some resume categories (e.g. HR, Healthcare, Teacher); these fall back to a generic default skill list and score conservatively.
- No LLM narration layer yet — SHAP output is currently shown directly rather than turned into recruiter-facing prose.

See [`docs/spec.md`](docs/spec.md) for the full specification, [`docs/decision.md`](docs/decision.md) for design decisions, and [`docs/rules.md`](docs/rules.md) for project rules.
