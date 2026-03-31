from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import os
import uuid

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

app = FastAPI(title="Questionnaire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

DATA_DIR = os.getenv("DATA_DIR", "/data/submissions")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Colors ────────────────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#8b5cf6")
PURPLE_LIGHT= colors.HexColor("#a78bfa")
BLUE        = colors.HexColor("#3b82f6")
BG_DARK     = colors.HexColor("#12121a")
BG_ROW      = colors.HexColor("#1a1a28")
TEXT        = colors.HexColor("#e2e8f0")
MUTED       = colors.HexColor("#94a3b8")
WHITE       = colors.white


class SubmissionPayload(BaseModel):
    company: str
    contact_name: str
    team_size: str
    industry: str
    use_cases: List[str]
    coding_tasks: Optional[List[str]] = []
    coding_languages: Optional[str] = ""
    ai_usage: str
    current_tools: Optional[str] = ""
    pain_point: str
    privacy: str
    integrations: List[str]
    num_users: int
    timeline: str
    priority_1: str
    priority_2: str
    priority_3: str
    other_requirements: Optional[str] = ""
    contact_method: str
    contact_email: EmailStr
    contact_phone: Optional[str] = ""


def build_pdf(payload: SubmissionPayload, filepath: str, submitted_at: str):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
    )

    base = getSampleStyleSheet()
    story = []

    # ── Styles ────────────────────────────────────────────────────────────────
    s_title = ParagraphStyle("title",
        fontSize=22, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=2*mm)

    s_subtitle = ParagraphStyle("subtitle",
        fontSize=10, fontName="Helvetica",
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=6*mm)

    s_section = ParagraphStyle("section",
        fontSize=8, fontName="Helvetica-Bold",
        textColor=PURPLE_LIGHT, spaceBefore=6*mm, spaceAfter=2*mm,
        leading=10)

    s_val = ParagraphStyle("val",
        fontSize=9, fontName="Helvetica",
        textColor=TEXT, leading=13, wordWrap="CJK")

    s_key = ParagraphStyle("key",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=MUTED, leading=13)

    s_footer = ParagraphStyle("footer",
        fontSize=8, fontName="Helvetica",
        textColor=MUTED, alignment=TA_CENTER, spaceBefore=6*mm)

    # ── Header banner ─────────────────────────────────────────────────────────
    W = A4[0] - 36*mm
    header_data = [[
        Paragraph("AI Platform — Sales Questionnaire", s_title),
    ]]
    header_table = Table(header_data, colWidths=[W])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PURPLE),
        ("ROUNDEDCORNERS", [6]),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("RIGHTPADDING",  (0,0), (-1,-1), 14),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"{payload.company}  ·  {payload.contact_name}", s_subtitle))

    def section_block(title: str, rows: list):
        """rows = list of (key, value) tuples"""
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=PURPLE, spaceAfter=1*mm))
        story.append(Paragraph(title.upper(), s_section))

        table_data = [
            [Paragraph(k, s_key), Paragraph(v or "—", s_val)]
            for k, v in rows
        ]
        col_w = [52*mm, W - 52*mm]
        t = Table(table_data, colWidths=col_w, repeatRows=0)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BG_DARK),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [BG_DARK, BG_ROW]),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW",     (0, 0), (-1, -2),
             0.3, colors.HexColor("#1e1e2e")),
            ("ROUNDEDCORNERS",[4]),
        ]))
        story.append(t)
        story.append(Spacer(1, 2*mm))

    # ── Section 1 ─────────────────────────────────────────────────────────────
    section_block("01 · Company & Team", [
        ("Company",       payload.company),
        ("Name & Role",   payload.contact_name),
        ("Team Size",     payload.team_size),
        ("Industry",      payload.industry),
    ])

    # ── Section 2 ─────────────────────────────────────────────────────────────
    use_cases_str = ", ".join(payload.use_cases) if payload.use_cases else "—"
    sec2_rows = [("Use Cases", use_cases_str)]
    if payload.coding_tasks:
        sec2_rows.append(("Coding Tasks",
                          ", ".join(payload.coding_tasks)))
        sec2_rows.append(("Languages",
                          payload.coding_languages or "—"))
    section_block("02 · Primary Use Case", sec2_rows)

    # ── Section 3 ─────────────────────────────────────────────────────────────
    integrations_str = (", ".join(payload.integrations)
                        if payload.integrations else "None")
    section_block("03 · Current Situation", [
        ("Using AI?",    payload.ai_usage),
        ("Current Tools",payload.current_tools or "—"),
        ("Pain Point",   payload.pain_point),
        ("Deployment",   payload.privacy),
        ("Integrations", integrations_str),
    ])

    # ── Section 4 ─────────────────────────────────────────────────────────────
    section_block("04 · Requirements & Timeline", [
        ("No. of Users",      str(payload.num_users)),
        ("Timeline",          payload.timeline),
        ("1st Priority",      payload.priority_1),
        ("2nd Priority",      payload.priority_2),
        ("3rd Priority",      payload.priority_3),
        ("Other Requirements",payload.other_requirements or "—"),
        ("Preferred Contact", payload.contact_method),
        ("Email",             str(payload.contact_email)),
        ("Phone",             payload.contact_phone or "—"),
    ])

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Paragraph(f"Submitted at {submitted_at}", s_footer))

    # ── Page background callback ──────────────────────────────────────────────
    def draw_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BG_DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)


@app.post("/api/submit")
async def submit_questionnaire(payload: SubmissionPayload):
    now = datetime.now(timezone.utc)
    submitted_at = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    # sanitize company name for use in filename
    safe_company = "".join(c if c.isalnum() or c in " -_" else "_" for c in payload.company).strip().replace(" ", "_")
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_company}.pdf"
    filepath = os.path.join(DATA_DIR, filename)
    build_pdf(payload, filepath, submitted_at)
    return {"status": "ok", "message": "Submission received. We'll be in touch soon."}


@app.get("/health")
def health():
    return {"status": "ok"}
