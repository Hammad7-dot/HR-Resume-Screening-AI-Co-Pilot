# SPEC — HR Resume Screening AI Co-Pilot

## 1. Problem Statement
Recruiters manually screen large volumes of resumes against a job description (JD), which is slow, inconsistent, and prone to bias. This Co-Pilot ranks and explains candidate fit while keeping a human recruiter in control of the final decision.

## 2. Users
- **Recruiter / HR Screener** — uploads JD + resumes, reviews AI shortlist, approves/rejects/modifies.
- **Hiring Manager (secondary)** — views final shortlist + report.

## 3. Data Modalities (3 required by rubric)
| # | Modality | Source | Use |
|---|----------|--------|-----|
| 1 | **Text** | Resume text, JD text | NLP feature extraction, keyword/skill matching, LLM reasoning |
| 2 | **PDF documents** | Uploaded resume PDFs | Layout-aware parsing (sections: education, experience, skills) — distinct from plain text since structure/formatting is extracted |
| 3 | **Tabular data** | Structured candidate features derived from parsing (years experience, education level, skill-overlap %, certifications count, keyword match score) | Input to the predictive deep learning model |

*(Synthetic/public resume + JD datasets only — no real candidate PII, per handbook's LinkedIn/PII caution.)*

## 4. Predictive Deep Learning Model (mandatory, non-LLM)
- **Model:** ANN (feed-forward) trained on the tabular structured features.
- **Output:** Fit Score (0–100) + category (Strong Fit / Moderate Fit / Weak Fit).
- **Why not LLM as predictor:** handbook requires LLMs be used only for reasoning/summarization/report generation, not as the primary predictive engine.

## 5. LLM Role (secondary, reasoning-only)
- Explains *why* the ANN gave a score in plain English (grounded in SHAP output, not free-generated).
- Drafts the final downloadable report.
- Answers recruiter follow-up questions about a candidate ("why was this person ranked lower?").

## 6. Human-in-the-Loop Workflow
1. AI produces ranked shortlist with Fit Score + explanation.
2. Recruiter reviews each candidate card: **Approve / Reject / Modify Score (with reason)**.
3. Recruiter decision + reason is logged (for audit + future retraining).
4. Only recruiter-approved candidates move to the final report.

## 7. Explainable AI
- SHAP values per candidate showing which features drove the score (e.g., "skill match +18, experience −5").
- Global feature importance chart across all candidates in a batch.
- Confidence score displayed alongside every prediction.

## 8. Web Application
- **Frontend:** React (candidate dashboard, JD upload, approve/reject UI, SHAP charts).
- **Backend:** FastAPI (parsing pipeline, ANN inference, SHAP, report generation).
- **Flow:** Upload JD → upload batch resumes (PDF) → parsing → ANN scoring → recruiter review (HITL) → downloadable report.

## 9. Deliverable Report
- Auto-generated PDF/DOCX per batch: JD summary, shortlisted candidates, Fit Scores, SHAP-based rationale, recruiter decisions/audit trail.

## 10. Business Model (rubric item)
- B2B SaaS for recruiting agencies / HR teams — per-seat or per-resume-processed pricing.
- Optional ATS (Applicant Tracking System) integration as upsell.
- Positioning: reduces screening time, adds an auditable, bias-flagging paper trail (useful for compliance).
