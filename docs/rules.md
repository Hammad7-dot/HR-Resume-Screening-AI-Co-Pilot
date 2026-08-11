# RULES — HR Resume Screening AI Co-Pilot

## A. Hackathon-mandatory rules (from handbook — non-negotiable)
1. Must process **at least 3 data modalities** → Text, PDF, Tabular (see spec.md §3).
2. Must include **at least one predictive deep learning model** (ANN/CNN/RNN family) → ANN on tabular features (see decision.md D1). LLMs cannot be the primary predictor.
3. LLM use is restricted to **reasoning, summarization, explanation, report generation** — never scoring/ranking directly.
4. Must include a **Human-in-the-Loop** step where a person approves/rejects/modifies AI output — no fully-automated hiring decisions.
5. Must provide **Explainable AI** — confidence scores + feature importance (SHAP) on every prediction, not just aggregate stats.
6. Must be a **working web application** — not a notebook or CLI-only demo.
7. Must generate a **downloadable PDF or DOCX report**.
8. Must present a **business model / commercialization strategy**.
9. Use only **public or synthetic** resume/candidate data — no real personal data, no LinkedIn scraping.

## B. Domain-specific rules (HR / hiring ethics)
10. No use of protected-attribute proxies (photo, name-implied ethnicity/gender, age indicators) as model features.
11. Every rejection/low score must have a visible, human-readable reason (SHAP-backed) — no "black box" rejections.
12. Recruiter's manual override always takes precedence over the AI score in the final report.
13. All recruiter decisions (approve/reject/modify + reason) are logged for auditability.

## C. Team working rules
14. Any new library/dataset must map to the "General Dataset Sources" list in the handbook or be clearly public/synthetic.
15. Every model prediction shown in the UI must have a paired confidence score and explanation — enforce this at the API contract level, not just in the frontend.
16. Scope changes go through decision.md — don't silently drop a mandatory requirement (A1–A9) without team agreement, since those are graded.
17. Before final submission, re-check every item in section A against the actual demo — treat it as the go/no-go checklist.
