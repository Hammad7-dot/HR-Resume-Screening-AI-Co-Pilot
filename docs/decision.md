# DECISIONS — HR Resume Screening AI Co-Pilot

Format: Decision → Alternatives considered → Reason chosen

---

### D1: Predictive model = ANN on tabular features (not CNN/RNN on raw resume text)
- **Alternatives:** LSTM/GRU over resume text embeddings; CNN over resume images.
- **Reason:** Tabular ANN is simpler, faster to train on limited synthetic data, easier to explain with SHAP, and clearly separates "predictive engine" from "LLM reasoning layer" as the rubric requires. RNN/CNN can be a stretch goal if time allows, but ANN is the guaranteed deliverable.

### D2: Third modality = PDF (layout) instead of image/audio/time-series
- **Alternatives:** Resume photos (image), interview audio, application-timeline (time-series).
- **Reason:** Photos on resumes risk demographic bias and add no scoring value (and are ethically risky for a hiring tool). PDF layout parsing (headers, sections, bullet structure) is a genuinely separate modality from raw text and is directly useful for accurate feature extraction.

### D3: LLM used only for explanation + report generation, never for scoring
- **Alternatives:** Let the LLM directly assign a fit score.
- **Reason:** Handbook explicitly disallows LLM as the primary predictive engine; also keeps scoring auditable/reproducible (ANN + SHAP) rather than dependent on prompt variance.

### D4: HITL = per-candidate approve/reject/modify, not batch-only approval
- **Alternatives:** Recruiter only approves/rejects the whole shortlist at once.
- **Reason:** Rubric rewards a real human-in-the-loop workflow; per-candidate control with a logged reason is more defensible and produces useful feedback data for retraining later.

### D5: Synthetic/public datasets only, no scraped LinkedIn data
- **Alternatives:** Scrape real candidate profiles for a richer demo.
- **Reason:** Handbook explicitly says LinkedIn data is not recommended; using public/synthetic resume datasets (Kaggle) avoids privacy/legal risk.

### D6: Tech stack — FastAPI backend + React frontend
- **Alternatives:** Streamlit/Gradio for speed; Flask backend.
- **Reason:** FastAPI gives clean async endpoints for parsing + inference and pairs well with a proper SHAP/dashboard UI in React, which looks more like a "working web application" than a notebook-style demo — matches the System Architecture and UX rubric lines.

### D7: Report generation = LLM-drafted, SHAP-grounded (not free-form)
- **Alternatives:** Pure template report with no LLM involvement.
- **Reason:** Using the LLM to turn structured SHAP + score data into readable prose satisfies the "LLM for report generation" allowance while keeping the underlying numbers trustworthy (LLM narrates, doesn't invent).

*(Add new decisions here as the team makes them — keep the same three-line format.)*
