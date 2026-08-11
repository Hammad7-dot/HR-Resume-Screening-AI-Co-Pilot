from pathlib import Path

import pdfplumber
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import store
from features import KNOWN_CATEGORIES
from model import scorer
import reports

app = FastAPI(title="HR Resume Screening AI Co-Pilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def extract_pdf_text(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(__import__("io").BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


@app.get("/api/categories")
def get_categories():
    return {"categories": KNOWN_CATEGORIES}


@app.post("/api/analyze-resume")
async def analyze_resume(category: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes are supported.")

    file_bytes = await file.read()
    resume_text = extract_pdf_text(file_bytes)
    if not resume_text.strip():
        raise HTTPException(422, "Could not extract text from this PDF (it may be a scanned image).")

    prediction = scorer.score_resume(resume_text, category)
    record = store.add_candidate(file.filename, category, prediction)
    return record


class DecisionIn(BaseModel):
    candidate_id: str
    decision: str  # "approve" | "reject" | "modify"
    reason: str
    modified_score: float | None = None


@app.post("/api/decision")
def submit_decision(body: DecisionIn):
    if body.decision not in ("approve", "reject", "modify"):
        raise HTTPException(400, "decision must be approve, reject, or modify")
    try:
        record = store.set_decision(body.candidate_id, body.decision, body.reason, body.modified_score)
    except KeyError:
        raise HTTPException(404, "candidate not found")
    return record


@app.get("/api/candidates")
def get_candidates():
    return {"candidates": store.list_candidates()}


@app.get("/api/report")
def download_report():
    pdf_buffer = reports.generate_report_pdf()
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume_screening_report.pdf"},
    )


# --- Serve the frontend last so it doesn't shadow /api routes ---
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
