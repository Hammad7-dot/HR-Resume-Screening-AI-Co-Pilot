"""
Streamlit-native alternative UI for the HR Resume Screening AI Co-Pilot.

Reuses the existing FastAPI backend's scoring/storage/report logic
in-process (no HTTP layer) so it can be deployed as a single app on
Streamlit Community Cloud, where only `streamlit run <file>.py` is
supported. See README.md -> "Streamlit Community Cloud Deployment".
"""
import io
import sys
from pathlib import Path

import pdfplumber
import streamlit as st

BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import store  # noqa: E402
import reports  # noqa: E402
from features import KNOWN_CATEGORIES  # noqa: E402
from model import scorer  # noqa: E402

st.set_page_config(page_title="HR Resume Screening — AI Co-Pilot", page_icon="✅", layout="wide")


def extract_pdf_text(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def fit_badge(fit_category: str) -> str:
    return {"Strong Fit": "🟢", "Moderate Fit": "🟡", "Weak Fit": "🔴"}.get(fit_category, "⚪")


st.title("HR Resume Screening — AI Co-Pilot")
st.caption("AI scores every resume. You decide who moves forward.")

st.header("1. Screen resumes")
category = st.selectbox("Job category (JD)", KNOWN_CATEGORIES)
uploaded_files = st.file_uploader(
    "Resume PDFs", type="pdf", accept_multiple_files=True, help="Drop resume PDFs here or click to browse"
)

if st.button("Analyze resumes", type="primary", disabled=not uploaded_files):
    progress = st.progress(0.0, text="Analyzing resumes...")
    errors = []
    for i, uploaded in enumerate(uploaded_files):
        try:
            resume_text = extract_pdf_text(uploaded.getvalue())
            if not resume_text.strip():
                errors.append(f"{uploaded.name}: could not extract text (may be a scanned image).")
                continue
            prediction = scorer.score_resume(resume_text, category)
            store.add_candidate(uploaded.name, category, prediction)
        except Exception as exc:  # noqa: BLE001 - surface any per-file failure without aborting the batch
            errors.append(f"{uploaded.name}: {exc}")
        progress.progress((i + 1) / len(uploaded_files), text=f"Analyzed {uploaded.name}")
    progress.empty()
    if errors:
        st.warning("Some resumes could not be analyzed:\n\n" + "\n".join(f"- {e}" for e in errors))
    else:
        st.toast("Resumes analyzed.", icon="✅")
    st.rerun()

st.divider()

header_col, report_col = st.columns([4, 1])
with header_col:
    st.header("2. Review & decide")
    st.caption("Human-in-the-loop")
with report_col:
    st.download_button(
        "Download report (PDF)",
        data=reports.generate_report_pdf(),
        file_name="resume_screening_report.pdf",
        mime="application/pdf",
    )

candidates = store.list_candidates()

if not candidates:
    st.info("No candidates yet — analyze a resume above to get started.")
else:
    screened = len(candidates)
    approved = sum(1 for c in candidates if c["decision"] == "approve")
    rejected = sum(1 for c in candidates if c["decision"] == "reject")
    pending = sum(1 for c in candidates if c["decision"] is None)
    scores = [c["prediction"]["fit_score"] for c in candidates]
    avg_score = f"{sum(scores) / len(scores):.1f}" if scores else "—"

    stat_cols = st.columns(5)
    stat_cols[0].metric("Screened", screened)
    stat_cols[1].metric("Approved", approved)
    stat_cols[2].metric("Rejected", rejected)
    stat_cols[3].metric("Pending", pending)
    stat_cols[4].metric("Avg score", avg_score)

    search_col, status_col, sort_col = st.columns([2, 1, 1])
    search = search_col.text_input("Search by filename...", value="")
    status_filter = status_col.selectbox(
        "Status", ["All statuses", "Pending", "Approve", "Reject", "Modify"]
    )
    sort_by = sort_col.selectbox(
        "Sort", ["Score: high to low", "Score: low to high", "Name: A-Z", "Confidence: high to low"]
    )

    filtered = candidates
    if search:
        filtered = [c for c in filtered if search.lower() in c["filename"].lower()]
    if status_filter == "Pending":
        filtered = [c for c in filtered if c["decision"] is None]
    elif status_filter != "All statuses":
        filtered = [c for c in filtered if c["decision"] == status_filter.lower()]

    if sort_by == "Score: high to low":
        filtered.sort(key=lambda c: c["prediction"]["fit_score"], reverse=True)
    elif sort_by == "Score: low to high":
        filtered.sort(key=lambda c: c["prediction"]["fit_score"])
    elif sort_by == "Name: A-Z":
        filtered.sort(key=lambda c: c["filename"].lower())
    elif sort_by == "Confidence: high to low":
        filtered.sort(key=lambda c: c["prediction"]["confidence"], reverse=True)

    if not filtered:
        st.info("No candidates match the current filter.")

    for candidate in filtered:
        pred = candidate["prediction"]
        cid = candidate["id"]
        with st.container(border=True):
            top_row = st.columns([3, 1, 1, 1])
            top_row[0].markdown(f"**{fit_badge(pred['fit_category'])} {candidate['filename']}**")
            top_row[0].caption(candidate["category"])
            top_row[1].metric("Fit score", f"{pred['fit_score']}/100")
            top_row[2].metric("Confidence", f"{pred['confidence']}%")
            top_row[3].metric("Experience", f"{pred['raw_features']['years_experience']} yrs")

            st.write(pred["narration"])
            with st.expander("Top SHAP features"):
                for f in pred["top_features"]:
                    sign = "+" if f["impact"] >= 0 else ""
                    st.write(f"- `{f['feature']}`: {sign}{f['impact']}")

            if candidate["decision"] is None:
                reason_key = f"reason_{cid}"
                modify_key = f"modify_open_{cid}"
                reason = st.text_input("Reason (required)", key=reason_key)

                btn_cols = st.columns(3)
                if btn_cols[0].button("Approve", key=f"approve_{cid}", disabled=not reason):
                    store.set_decision(cid, "approve", reason)
                    st.rerun()
                if btn_cols[1].button("Reject", key=f"reject_{cid}", disabled=not reason):
                    store.set_decision(cid, "reject", reason)
                    st.rerun()
                if btn_cols[2].button("Modify Score", key=f"modify_btn_{cid}"):
                    st.session_state[modify_key] = True

                if st.session_state.get(modify_key):
                    new_score = st.number_input(
                        "New score (0-100)", min_value=0.0, max_value=100.0,
                        value=float(pred["fit_score"]), key=f"score_{cid}",
                    )
                    save_col, cancel_col = st.columns(2)
                    if save_col.button("Save", key=f"save_{cid}", disabled=not reason):
                        store.set_decision(cid, "modify", reason, new_score)
                        st.session_state[modify_key] = False
                        st.rerun()
                    if cancel_col.button("Cancel", key=f"cancel_{cid}"):
                        st.session_state[modify_key] = False
                        st.rerun()
            else:
                stamp = {"approve": "✅ Approved", "reject": "❌ Rejected", "modify": "✏️ Modified"}[candidate["decision"]]
                st.success(f"{stamp} — {candidate['decision_reason']}")
