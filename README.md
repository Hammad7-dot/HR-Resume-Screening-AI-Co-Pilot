# HR Resume Screening — AI Co-Pilot

An AI-assisted resume screening web app that scores candidate fit against a job category with a trained neural network, explains every score with SHAP, and requires a recruiter to approve, reject, or modify each result before it counts as final — keeping a human in the loop at all times.

**🚀 Live demo:** [hr-resume-screening-ai-co-pilot-nrhj2uka3wfbjxsqkjcfv2.streamlit.app](https://hr-resume-screening-ai-co-pilot-nrhj2uka3wfbjxsqkjcfv2.streamlit.app/)

## Overview

Recruiters manually screening large volumes of resumes is slow, inconsistent, and prone to bias. This Co-Pilot parses resume PDFs, extracts structured features, scores fit with a trained ANN, and explains *why* using SHAP — while a recruiter stays in control of every final decision.

## Features

- **Multi-modal input** — resume PDFs (layout-aware parsing), resume text, and structured tabular features (years of experience, education level, certifications, skill count, category).
- **Predictive deep learning model** — a feed-forward ANN (PyTorch) produces the Fit Score (0–100); the LLM, if used, only narrates — it never predicts.
- **Explainable AI** — calibrated confidence score (MC-Dropout) and top SHAP features per prediction, shown in the UI and in the exported report.
- **Human-in-the-loop** — nothing is final until a recruiter clicks Approve, Reject, or Modify Score with a reason; every decision is logged with a timestamp for audit.
- **Downloadable report** — auto-generated PDF shortlist with Fit Scores, SHAP rationale, and the recruiter audit trail.
- **Batch overview** — a stats bar (screened / approved / rejected / pending / average score) plus search, status filter, and sort controls for reviewing larger batches quickly.
- **Toast feedback** — non-blocking confirmations when a resume finishes analyzing or a decision is saved.

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

## Streamlit Community Cloud deployment

**Live app:** https://hr-resume-screening-ai-co-pilot-nrhj2uka3wfbjxsqkjcfv2.streamlit.app/

`streamlit_app.py` is a Streamlit-native alternative UI that reuses the same scoring, storage, and report logic (`backend/model.py`, `features.py`, `store.py`, `reports.py`) directly in-process — no separate API server. This is what makes the app deployable on [Streamlit Community Cloud](https://share.streamlit.io), which only runs `streamlit run <file>.py` and can't host a standalone FastAPI server.

Run it locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Deploy it:

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, pick this repository and branch.
4. Set **Main file path** to `streamlit_app.py`.
5. Click **Deploy**.

**Known limitation:** candidate/decision data is stored in `backend/data/candidates.json` on the container's local filesystem. Streamlit Community Cloud's filesystem is ephemeral — it resets on redeploys and when the app sleeps/wakes — so this is fine for a live demo but not for persistent production storage. The FastAPI deployment path (above) has the same limitation; swapping in a real database is future work, not covered here.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000  # not required to run tests
python -m pytest tests/ -v
```

Covers feature engineering (`features.py`), the candidate/decision store (`store.py`), and the REST API (categories, resume analysis, decisions, report download) via FastAPI's `TestClient`. Tests run against the real trained model artifacts and write to a throwaway data file, so they never touch `backend/data/candidates.json`. CI runs this suite on every push via `.github/workflows/tests.yml`.

## Tech stack

- **Backend:** FastAPI, PyTorch, SHAP, scikit-learn, pandas, pdfplumber, ReportLab
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **Storage:** JSON-file candidate + decision store

## Known limitations

- `skills_count` dominates predictions — years of experience and education level move the score much less, by design of the synthetic training label (skill-overlap %).
- Skill-bank keyword coverage is currently thin for some resume categories (e.g. HR, Healthcare, Teacher); these fall back to a generic default skill list and score conservatively.
- No LLM narration layer yet — SHAP output is currently shown directly rather than turned into recruiter-facing prose.

See [`docs/spec.md`](docs/spec.md) for the full specification, [`docs/decision.md`](docs/decision.md) for design decisions, and [`docs/rules.md`](docs/rules.md) for project rules.

## License

MIT — see [`LICENSE`](LICENSE).
