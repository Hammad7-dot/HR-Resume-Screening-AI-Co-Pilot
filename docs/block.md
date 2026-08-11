# BLOCK — Blockers, Risks & Open Questions

## Current Blockers
*(none yet — update as they come up during the build)*

| Blocker | Impact | Owner | Status |
|---|---|---|---|
| — | — | — | — |

## Risks to Watch
| Risk | Why it matters | Mitigation |
|---|---|---|
| Resume PDF parsing is inconsistent across formats/templates | Breaks the "PDF modality" and downstream tabular features | Pick a small, curated set of resume templates from the Kaggle dataset; add fallback plain-text extraction if layout parsing fails |
| ANN trained on synthetic/small data may give unstable or non-sensical Fit Scores | Hurts the Deep Learning Implementation + Explainable AI rubric lines | Keep the label definition simple (e.g., skill-overlap-driven), validate SHAP output makes intuitive sense on a few hand-checked resumes before demo |
| SHAP computation can be slow on the fly for a large batch | Live demo lag | Precompute SHAP for the demo dataset; cache results |
| LLM might drift into producing a "score" or a hiring recommendation in its own words | Violates rule A3 (LLM can't be the predictive engine) | Constrain LLM prompt strictly to narrating the ANN's numbers/SHAP values it's given — never asking it to invent a score |
| Report generation (PDF/DOCX) left until the last day | Mandatory deliverable (rule A7) — high risk if rushed | Build a bare-bones template report early, polish later |
| Team unclear on final demo data source (real vs synthetic resumes) | Could violate rule A9 if someone grabs real LinkedIn/resume data | Confirm dataset choice as a team before scraping/parsing anything |

## Open Questions
- [ ] Which Kaggle resume dataset are we using — one dataset for all roles, or role-specific JD/resume pairs?
- [ ] What exactly counts as a "Strong / Moderate / Weak Fit" threshold on the Fit Score — needs a team decision (log it in decision.md once settled).
- [ ] Does the HITL review happen one-candidate-at-a-time or as a batch table with inline actions? (affects frontend build time)
- [ ] Who owns the SHAP integration vs. who owns the report generation — need to split so they're not both blocked on the same person.

*(Keep this file updated as the build progresses — move resolved blockers out, add new ones as they surface.)*
