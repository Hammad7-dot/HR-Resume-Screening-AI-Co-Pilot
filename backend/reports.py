"""
Generates the downloadable PDF report: JD/category summary, shortlisted
(recruiter-approved) candidates, their fit scores + SHAP rationale, and
the recruiter decision audit trail.
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

import store


def generate_report_pdf() -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18)
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)

    elements = []
    elements.append(Paragraph("HR Resume Screening — Shortlist Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", small))
    elements.append(Spacer(1, 0.2 * inch))

    all_candidates = store.list_candidates()
    approved = [c for c in all_candidates if c["decision"] == "approve"]
    rejected = [c for c in all_candidates if c["decision"] == "reject"]
    modified = [c for c in all_candidates if c["decision"] == "modify"]

    elements.append(Paragraph(
        f"Batch summary: {len(all_candidates)} candidates screened — "
        f"{len(approved)} approved, {len(rejected)} rejected, {len(modified)} modified by recruiter.",
        body,
    ))
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Approved Candidates", h2))
    if not approved:
        elements.append(Paragraph("No candidates have been approved yet.", body))
    else:
        table_data = [["Candidate", "Category", "AI Fit Score", "Confidence", "Recruiter Note"]]
        for c in approved:
            pred = c["prediction"]
            score = c["modified_score"] if c["modified_score"] is not None else pred["fit_score"]
            table_data.append([
                c["filename"],
                c["category"],
                f"{score} ({pred['fit_category']})",
                f"{pred['confidence']}%",
                c["decision_reason"] or "-",
            ])
        t = Table(table_data, colWidths=[1.6 * inch, 1.3 * inch, 1.3 * inch, 0.9 * inch, 1.4 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b3a55")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
        ]))
        elements.append(t)

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Explainability — Why Each Approved Candidate Scored As They Did", h2))
    for c in approved:
        pred = c["prediction"]
        elements.append(Paragraph(f"<b>{c['filename']}</b> — {pred['fit_score']} ({pred['fit_category']}), "
                                   f"{pred['confidence']}% confidence", body))
        if pred.get("narration"):
            elements.append(Paragraph(pred["narration"], small))
        for feat in pred["top_features"]:
            direction = "increased" if feat["impact"] > 0 else "decreased"
            elements.append(Paragraph(
                f"&nbsp;&nbsp;• {feat['feature']} {direction} the score (impact {feat['impact']:+.2f})", small
            ))
        elements.append(Spacer(1, 0.1 * inch))

    if rejected or modified:
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("Recruiter Decision Audit Trail (all candidates)", h2))
        audit_data = [["Candidate", "AI Score", "Decision", "Reason", "Decided At"]]
        for c in all_candidates:
            pred = c["prediction"]
            audit_data.append([
                c["filename"],
                str(pred["fit_score"]),
                c["decision"] or "pending",
                (c["decision_reason"] or "-")[:40],
                (c["decided_at"] or "-")[:19],
            ])
        t2 = Table(audit_data, colWidths=[1.4 * inch, 0.8 * inch, 0.9 * inch, 1.8 * inch, 1.4 * inch])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#555")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t2)

    doc.build(elements)
    buffer.seek(0)
    return buffer
