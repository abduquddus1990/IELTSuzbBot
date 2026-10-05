"""ReportLab Multi-Page PDF Certificate & Diagnostic Error Workbook Generator ($0.00 API Cost).

Generates a professional, multi-page A4 PDF report for IELTS & Uzbekistan National CEFR
(Bilimni baholash agentligi — BBA Multi-Level) mock exams:

- **Page 1: Executive Mock Certificate & Dual-Scale Score Summary**
  - Deep Navy (`#0F172A`), Slate (`#1E293B`), Royal Gold (`#D97706`), Emerald (`#059669`),
    and Soft Neutral (`#F8FAFC`) aesthetic theme.
  - Executive Header Banner with Platform Title, Exam Type Badge (`IELTS ACADEMIC` /
    `UZBMB MULTI-LEVEL CEFR`), Candidate Info, Exam Date, and Report ID.
  - Hero Dual-Scale Score Card displaying:
    1. Overall IELTS Band (`0.0 - 9.0`)
    2. CEFR Proficiency Level (`BELOW_B1` / `B1` / `B2` / `C1`)
    3. Uzbekistan BBA Standard Score (`0 - 75`)
  - 4-Skill Breakdown Table (`Listening`, `Reading`, `Writing`, `Speaking`) with custom
    ReportLab vector progress bars (`Drawing` + `Rect`), Raw Score, IELTS Band, and BBA Score.
  - Analytical 4-Criteria Sub-score Breakdown for both Writing and Speaking.
  - Verification QR Code (`QrCodeWidget` inside a `Drawing`) + Mandatory Legal Disclaimer Box.

- **Page 2+: Xatolar Daftari (Detailed Error Analysis) & Band Booster Vocabulary**
  - Writing & Speaking `detailed_errors` table (`#`, `Modul`, `Xato jumla (Original)`,
    `To'g'ri shakl (Correction)`, `O'zbekcha izoh va qoida`) with automatic `Paragraph` wrapping.
  - `band_booster_vocabulary` table (`#`, `Modul`, `Ishlatilgan oddiy so'z (Simple)`,
    `Tavsiya etilgan C1 / Band 8.0+ muqobil (Advanced)`).
  - Speaking Fluency & Pronunciation diagnostic coaching in Uzbek.
"""

from __future__ import annotations

import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import BASE_DIR, settings
from app.schemas.report import FullExamReportData, band_to_cefr_75_score
from app.schemas.writing import BandBoosterVocabulary, DetailedError

# =====================================================================
# 1. COLOR PALETTE & CONSTANTS
# =====================================================================

COLOR_DEEP_NAVY = colors.HexColor("#7A0C1E")  # brand maroon (red theme)
COLOR_SLATE = colors.HexColor("#1E293B")
COLOR_SLATE_MUTED = colors.HexColor("#475569")
COLOR_ROYAL_GOLD = colors.HexColor("#D97706")
COLOR_GOLD_LIGHT = colors.HexColor("#FEF3C7")
COLOR_EMERALD = colors.HexColor("#059669")
COLOR_EMERALD_LIGHT = colors.HexColor("#D1FAE5")
COLOR_BLUE_ACCENT = colors.HexColor("#C8102E")
COLOR_CRIMSON = colors.HexColor("#DC2626")
COLOR_CRIMSON_LIGHT = colors.HexColor("#FEE2E2")
COLOR_SOFT_NEUTRAL = colors.HexColor("#F8FAFC")
COLOR_ROW_ALT = colors.HexColor("#F1F5F9")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_TRACK_BG = colors.HexColor("#E2E8F0")
COLOR_WHITE = colors.HexColor("#FFFFFF")

MANDATORY_LEGAL_DISCLAIMER = (
    "Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool). "
    "Ushbu hujjat rasmiy Cambridge, IDP, British Council yoki Bilimni baholash "
    "agentligi (BBA) sertifikati hisoblanmaydi."
)


def _clean_and_escape(text: str | None) -> str:
    """Normalize Unicode apostrophes/quotes for Helvetica compatibility and escape XML entities."""
    if not text:
        return ""
    normalized = (
        str(text)
        .replace("\u02bb", "'")
        .replace("\u02bc", "'")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", " - ")
    )
    return escape(normalized)


# =====================================================================
# 2. VECTOR GRAPHICS HELPERS (PROGRESS BARS & QR CODE)
# =====================================================================


def build_score_progress_bar(
    score: float,
    max_score: float = 9.0,
    width: float = 120.0,
    height: float = 10.0,
) -> Drawing:
    """Build a vector horizontal progress bar using ReportLab `Drawing` and `Rect`."""
    safe_max = max(0.01, float(max_score))
    clamped = max(0.0, min(safe_max, float(score)))
    ratio = clamped / safe_max
    fill_width = round(width * ratio, 2)

    if ratio >= 0.75:
        bar_color = COLOR_EMERALD
    elif ratio >= 0.55:
        bar_color = COLOR_BLUE_ACCENT
    elif ratio >= 0.40:
        bar_color = COLOR_ROYAL_GOLD
    else:
        bar_color = COLOR_CRIMSON

    drawing = Drawing(width, height + 2)
    # Background track
    drawing.add(
        Rect(
            0,
            1,
            width,
            height,
            rx=3,
            ry=3,
            fillColor=COLOR_TRACK_BG,
            strokeColor=COLOR_BORDER,
            strokeWidth=0.4,
        )
    )
    # Foreground progress fill
    if fill_width > 0:
        drawing.add(
            Rect(
                0,
                1,
                max(4.0, fill_width),
                height,
                rx=3,
                ry=3,
                fillColor=bar_color,
                strokeColor=None,
                strokeWidth=0,
            )
        )
    # Percentage / ratio label inside or beside bar
    pct_text = f"{int(round(ratio * 100))}%"
    drawing.add(
        String(
            width - 22,
            3,
            pct_text,
            fontName="Helvetica-Bold",
            fontSize=6.5,
            fillColor=COLOR_DEEP_NAVY if ratio < 0.82 else COLOR_WHITE,
        )
    )
    return drawing


def build_qr_code_drawing(url: str, size: float = 64.0) -> Drawing:
    """Build a vector QR code `Drawing` using ReportLab's `QrCodeWidget`."""
    qr_url = (url or "https://t.me/ielts_cefr_mock_ai_bot").strip()
    qr_widget = QrCodeWidget(qr_url)
    bounds = qr_widget.getBounds()
    qr_width = max(1.0, bounds[2] - bounds[0])
    qr_height = max(1.0, bounds[3] - bounds[1])

    drawing = Drawing(
        size,
        size,
        transform=[size / qr_width, 0, 0, size / qr_height, 0, 0],
    )
    drawing.add(qr_widget)
    return drawing


# =====================================================================
# 3. PARAGRAPH STYLES & PAGE CANVAS DECORATION
# =====================================================================


def _build_styles() -> dict[str, ParagraphStyle]:
    """Create custom ReportLab ParagraphStyles for the Certificate and Error Workbook."""
    base = getSampleStyleSheet()
    return {
        "header_title": ParagraphStyle(
            "HeaderTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=COLOR_WHITE,
        ),
        "header_subtitle": ParagraphStyle(
            "HeaderSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_GOLD_LIGHT,
        ),
        "badge_text": ParagraphStyle(
            "BadgeText",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
            textColor=COLOR_GOLD_LIGHT,
        ),
        "meta_label": ParagraphStyle(
            "MetaLabel",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_SLATE_MUTED,
        ),
        "meta_value": ParagraphStyle(
            "MetaValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=COLOR_DEEP_NAVY,
        ),
        "hero_label": ParagraphStyle(
            "HeroLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=COLOR_GOLD_LIGHT,
        ),
        "hero_value": ParagraphStyle(
            "HeroValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=COLOR_WHITE,
        ),
        "hero_sub": ParagraphStyle(
            "HeroSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=COLOR_TRACK_BG,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=COLOR_DEEP_NAVY,
            spaceBefore=4,
            spaceAfter=4,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_WHITE,
        ),
        "table_header_center": ParagraphStyle(
            "TableHeaderCenter",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=COLOR_WHITE,
        ),
        "cell_text": ParagraphStyle(
            "CellText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=COLOR_SLATE,
        ),
        "cell_bold": ParagraphStyle(
            "CellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=COLOR_DEEP_NAVY,
        ),
        "cell_center_bold": ParagraphStyle(
            "CellCenterBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=COLOR_DEEP_NAVY,
        ),
        "cell_error_orig": ParagraphStyle(
            "CellErrorOrig",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_CRIMSON,
        ),
        "cell_error_fix": ParagraphStyle(
            "CellErrorFix",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=COLOR_EMERALD,
        ),
        "cell_uz_explain": ParagraphStyle(
            "CellUzExplain",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_SLATE,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=COLOR_SLATE_MUTED,
        ),
    }


def _draw_page_chrome(canvas, doc) -> None:
    """Draw subtle decorative page border and page number footer on every page."""
    canvas.saveState()
    page_width, page_height = A4

    # Top Royal Gold accent bar
    canvas.setFillColor(COLOR_ROYAL_GOLD)
    canvas.rect(20, page_height - 16, page_width - 40, 3, fill=1, stroke=0)

    # Outer thin border frame
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.6)
    canvas.rect(20, 18, page_width - 40, page_height - 34, fill=0, stroke=1)

    # Bottom page number & short legal watermark
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(COLOR_SLATE_MUTED)
    canvas.drawString(
        28,
        8,
        "IELTS & CEFR Mock AI | Mustaqil AI baholash va tayyorgarlik vositasi ($0 Local ReportLab Engine)",
    )
    canvas.drawRightString(page_width - 28, 8, f"Sahifa {doc.page}")
    canvas.restoreState()


# =====================================================================
# 4. PDF REPORT GENERATOR SERVICE
# =====================================================================


class PDFReportGeneratorService:
    """ReportLab multi-page PDF Certificate & Diagnostic Error Workbook generator."""

    def __init__(self, default_output_dir: str | Path | None = None) -> None:
        raw_dir = default_output_dir or settings.PDF_OUTPUT_DIR
        dir_path = Path(raw_dir)
        if not dir_path.is_absolute():
            dir_path = BASE_DIR / dir_path
        self.output_dir = dir_path

    def _build_page1_elements(
        self,
        report_data: FullExamReportData,
        styles: dict[str, ParagraphStyle],
        usable_width: float,
    ) -> list:
        """Assemble Page 1: Executive Certificate, Dual-Scale Hero Card, 4-Skill Bars, Criteria, QR & Disclaimer."""
        story: list = []
        scores = report_data.scores

        exam_badge = (
            "IELTS ACADEMIC MOCK"
            if report_data.exam_type == "IELTS"
            else "UZBMB MULTI-LEVEL CEFR MOCK"
        )

        # 1. Executive Header Banner Table
        header_left = [
            Paragraph(
                "IELTS &amp; CEFR MOCK AI — DIAGNOSTIC REPORT",
                styles["header_title"],
            ),
            Spacer(1, 2),
            Paragraph(
                "Xalqaro IELTS (0.0-9.0) va Milliy BBA Multi-Level (0-75) Diagnostik Tahlil Sertifikati",
                styles["header_subtitle"],
            ),
        ]
        header_right = [
            Paragraph(_clean_and_escape(exam_badge), styles["badge_text"]),
            Spacer(1, 2),
            Paragraph(
                f"ID: {_clean_and_escape(report_data.report_id)}",
                styles["badge_text"],
            ),
        ]
        header_table = Table(
            [[header_left, header_right]],
            colWidths=[usable_width * 0.68, usable_width * 0.32],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_DEEP_NAVY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LINEBELOW", (0, 0), (-1, -1), 2.0, COLOR_ROYAL_GOLD),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 6))

        # 2. Candidate Metadata Bar
        tg_display = (
            f"@{report_data.candidate_telegram_id}"
            if report_data.candidate_telegram_id
            else "Web / Telegram Mini App"
        )
        meta_rows = [
            [
                Paragraph("NOMZOD (CANDIDATE):", styles["meta_label"]),
                Paragraph(_clean_and_escape(report_data.candidate_name), styles["meta_value"]),
                Paragraph("IMTIHON SANASI (DATE):", styles["meta_label"]),
                Paragraph(_clean_and_escape(report_data.exam_date), styles["meta_value"]),
            ],
            [
                Paragraph("TELEGRAM / FOYDALANUVCHI:", styles["meta_label"]),
                Paragraph(_clean_and_escape(tg_display), styles["meta_value"]),
                Paragraph("IMTIHON FORMATI:", styles["meta_label"]),
                Paragraph(_clean_and_escape(report_data.exam_type), styles["meta_value"]),
            ],
        ]
        meta_table = Table(
            meta_rows,
            colWidths=[
                usable_width * 0.23,
                usable_width * 0.31,
                usable_width * 0.22,
                usable_width * 0.24,
            ],
        )
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_SOFT_NEUTRAL),
                    ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # 3. Hero Dual-Scale Score Card
        col_third = usable_width / 3.0
        hero_cells = [
            [
                [
                    Paragraph("OVERALL IELTS BAND", styles["hero_label"]),
                    Spacer(1, 3),
                    Paragraph(f"{scores.overall_band:.1f} / 9.0", styles["hero_value"]),
                    Spacer(1, 2),
                    Paragraph("Rasmiy .25 / .75 yaxlitlash qoidasi", styles["hero_sub"]),
                ],
                [
                    Paragraph("CEFR PROFICIENCY LEVEL", styles["hero_label"]),
                    Spacer(1, 3),
                    Paragraph(_clean_and_escape(scores.cefr_level.replace("BELOW_B1", "Below B1")), styles["hero_value"]),
                    Spacer(1, 2),
                    Paragraph("Umumyevropa til bilish darajasi", styles["hero_sub"]),
                ],
                [
                    Paragraph("UZBMB (BBA) STANDARD SCORE", styles["hero_label"]),
                    Spacer(1, 3),
                    Paragraph(f"{scores.overall_score_75:.1f} / 75", styles["hero_value"]),
                    Spacer(1, 2),
                    Paragraph("Milliy Multi-Level 0-75 shkalasi", styles["hero_sub"]),
                ],
            ]
        ]
        hero_table = Table(hero_cells, colWidths=[col_third, col_third, col_third])
        hero_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), COLOR_SLATE),
                    ("BACKGROUND", (1, 0), (1, 0), COLOR_DEEP_NAVY),
                    ("BACKGROUND", (2, 0), (2, 0), COLOR_SLATE),
                    ("BOX", (0, 0), (-1, -1), 1.2, COLOR_ROYAL_GOLD),
                    ("LINEBEFORE", (1, 0), (1, 0), 0.8, COLOR_ROYAL_GOLD),
                    ("LINEBEFORE", (2, 0), (2, 0), 0.8, COLOR_ROYAL_GOLD),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(hero_table)
        story.append(Spacer(1, 8))

        # 4. 4-Skill Breakdown Table with Vector Progress Bars
        story.append(
            Paragraph(
                "1. TO'RTTA KO'NIKMA BO'YICHA NATIJALAR (4-SKILL SCORE BREAKDOWN)",
                styles["section_heading"],
            )
        )
        skill_rows = [
            [
                Paragraph("Ko'nikma (Skill)", styles["table_header"]),
                Paragraph("To'g'ri javob (Raw)", styles["table_header_center"]),
                Paragraph("IELTS Band (0-9)", styles["table_header_center"]),
                Paragraph("BBA Ball (0-75)", styles["table_header_center"]),
                Paragraph("Vizual Ko'rsatkich (Progress)", styles["table_header"]),
            ],
            [
                Paragraph("Listening (Tinglab tushunish)", styles["cell_bold"]),
                Paragraph(f"{scores.listening_raw} / 40", styles["cell_center_bold"]),
                Paragraph(f"{scores.listening_band:.1f}", styles["cell_center_bold"]),
                Paragraph(f"{scores.listening_score_75:.1f} / 75", styles["cell_center_bold"]),
                build_score_progress_bar(scores.listening_band, 9.0, width=130.0, height=10.0),
            ],
            [
                Paragraph("Reading (O'qib tushunish)", styles["cell_bold"]),
                Paragraph(f"{scores.reading_raw} / 40", styles["cell_center_bold"]),
                Paragraph(f"{scores.reading_band:.1f}", styles["cell_center_bold"]),
                Paragraph(f"{scores.reading_score_75:.1f} / 75", styles["cell_center_bold"]),
                build_score_progress_bar(scores.reading_band, 9.0, width=130.0, height=10.0),
            ],
            [
                Paragraph("Writing (Yozma nutq — T1+T2)", styles["cell_bold"]),
                Paragraph("AI Rubric", styles["cell_center_bold"]),
                Paragraph(f"{scores.writing_band:.1f}", styles["cell_center_bold"]),
                Paragraph(f"{scores.writing_score_75:.1f} / 75", styles["cell_center_bold"]),
                build_score_progress_bar(scores.writing_band, 9.0, width=130.0, height=10.0),
            ],
            [
                Paragraph("Speaking (Og'zaki nutq — P1-P3)", styles["cell_bold"]),
                Paragraph("Whisper + AI", styles["cell_center_bold"]),
                Paragraph(f"{scores.speaking_band:.1f}", styles["cell_center_bold"]),
                Paragraph(f"{scores.speaking_score_75:.1f} / 75", styles["cell_center_bold"]),
                build_score_progress_bar(scores.speaking_band, 9.0, width=130.0, height=10.0),
            ],
        ]
        skill_table = Table(
            skill_rows,
            colWidths=[
                usable_width * 0.30,
                usable_width * 0.15,
                usable_width * 0.14,
                usable_width * 0.15,
                usable_width * 0.26,
            ],
        )
        skill_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_DEEP_NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ROW_ALT]),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(skill_table)
        story.append(Spacer(1, 8))

        # 5. Writing & Speaking 4-Criteria Analytical Breakdown Table
        story.append(
            Paragraph(
                "2. WRITING VA SPEAKING MEZONLARI TAHLILI (ANALYTICAL RUBRIC CRITERIA)",
                styles["section_heading"],
            )
        )
        w_eval = report_data.writing_evaluation
        s_eval = report_data.speaking_evaluation

        w_ta = f"{w_eval.criteria_scores.task_achievement:.1f}" if w_eval else "-"
        w_cc = f"{w_eval.criteria_scores.coherence_cohesion:.1f}" if w_eval else "-"
        w_lr = f"{w_eval.criteria_scores.lexical_resource:.1f}" if w_eval else "-"
        w_gr = f"{w_eval.criteria_scores.grammatical_range_accuracy:.1f}" if w_eval else "-"
        w_sub = (
            f"Task 1: {w_eval.task_1_score:.1f} | Task 2: {w_eval.task_2_score:.1f}"
            if w_eval
            else "Topshirilmagan"
        )

        s_fc = f"{s_eval.criteria_scores.fluency_coherence:.1f}" if s_eval else "-"
        s_lr = f"{s_eval.criteria_scores.lexical_resource:.1f}" if s_eval else "-"
        s_gr = f"{s_eval.criteria_scores.grammatical_range_accuracy:.1f}" if s_eval else "-"
        s_pr = f"{s_eval.criteria_scores.pronunciation:.1f}" if s_eval else "-"
        s_sub = (
            f"P1: {s_eval.part_1_score:.1f} | P2: {s_eval.part_2_score:.1f} | P3: {s_eval.part_3_score:.1f}"
            if s_eval
            else "Topshirilmagan"
        )

        crit_rows = [
            [
                Paragraph("Writing Mezonlari (25% dan)", styles["table_header"]),
                Paragraph("Ball", styles["table_header_center"]),
                Paragraph("Speaking Mezonlari (25% dan)", styles["table_header"]),
                Paragraph("Ball", styles["table_header_center"]),
            ],
            [
                Paragraph("Task Achievement / Response", styles["cell_text"]),
                Paragraph(w_ta, styles["cell_center_bold"]),
                Paragraph("Fluency &amp; Coherence", styles["cell_text"]),
                Paragraph(s_fc, styles["cell_center_bold"]),
            ],
            [
                Paragraph("Coherence &amp; Cohesion", styles["cell_text"]),
                Paragraph(w_cc, styles["cell_center_bold"]),
                Paragraph("Lexical Resource", styles["cell_text"]),
                Paragraph(s_lr, styles["cell_center_bold"]),
            ],
            [
                Paragraph("Lexical Resource (Vocabulary)", styles["cell_text"]),
                Paragraph(w_lr, styles["cell_center_bold"]),
                Paragraph("Grammatical Range &amp; Accuracy", styles["cell_text"]),
                Paragraph(s_gr, styles["cell_center_bold"]),
            ],
            [
                Paragraph("Grammatical Range &amp; Accuracy", styles["cell_text"]),
                Paragraph(w_gr, styles["cell_center_bold"]),
                Paragraph("Pronunciation", styles["cell_text"]),
                Paragraph(s_pr, styles["cell_center_bold"]),
            ],
            [
                Paragraph(f"Writing qismlar: {_clean_and_escape(w_sub)}", styles["cell_bold"]),
                Paragraph(f"{scores.writing_band:.1f}", styles["cell_center_bold"]),
                Paragraph(f"Speaking qismlar: {_clean_and_escape(s_sub)}", styles["cell_bold"]),
                Paragraph(f"{scores.speaking_band:.1f}", styles["cell_center_bold"]),
            ],
        ]
        crit_table = Table(
            crit_rows,
            colWidths=[
                usable_width * 0.38,
                usable_width * 0.12,
                usable_width * 0.38,
                usable_width * 0.12,
            ],
        )
        crit_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SLATE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [COLOR_WHITE, COLOR_ROW_ALT]),
                    ("BACKGROUND", (0, -1), (-1, -1), COLOR_GOLD_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(crit_table)
        story.append(Spacer(1, 10))

        # 6. Verification QR Code + Mandatory Legal Disclaimer Footer Box
        qr_drawing = build_qr_code_drawing(report_data.verification_url, size=62.0)
        raw_disclaimer = (report_data.disclaimer_text or MANDATORY_LEGAL_DISCLAIMER).strip()
        if "Mustaqil AI baholash va tayyorgarlik vositasi" not in raw_disclaimer:
            raw_disclaimer = f"{MANDATORY_LEGAL_DISCLAIMER} {raw_disclaimer}"

        footer_info = [
            Paragraph(
                "<b>YURIDIK OGOHLANTIRISH (LEGAL DISCLAIMER) VA TEKSHIRUV QR KODI:</b>",
                styles["cell_bold"],
            ),
            Spacer(1, 2),
            Paragraph(_clean_and_escape(raw_disclaimer), styles["disclaimer"]),
            Spacer(1, 3),
            Paragraph(
                f"Tekshiruv manzili: {_clean_and_escape(report_data.verification_url)} | "
                "2-sahifada Xatolar Daftari (Detailed Error Analysis) va C1 Band Booster lug'ati keltirilgan.",
                styles["disclaimer"],
            ),
        ]
        footer_table = Table(
            [[qr_drawing, footer_info]],
            colWidths=[76.0, usable_width - 76.0],
        )
        footer_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_SOFT_NEUTRAL),
                    ("BOX", (0, 0), (-1, -1), 0.8, COLOR_ROYAL_GOLD),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(footer_table)
        return story

    def _build_page2_workbook_elements(
        self,
        report_data: FullExamReportData,
        styles: dict[str, ParagraphStyle],
        usable_width: float,
    ) -> list:
        """Assemble Page 2+: Xatolar Daftari (Detailed Errors), Band Booster Vocabulary & Speaking Coaching."""
        story: list = [PageBreak()]

        # Page 2 Banner
        wb_banner = Table(
            [
                [
                    Paragraph(
                        "XATOLAR DAFTARI VA SO'Z BOYLIGINI OSHIRISH (ERROR WORKBOOK &amp; BAND BOOSTER)",
                        styles["header_title"],
                    ),
                    Paragraph(
                        f"ID: {_clean_and_escape(report_data.report_id)}",
                        styles["badge_text"],
                    ),
                ]
            ],
            colWidths=[usable_width * 0.76, usable_width * 0.24],
        )
        wb_banner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_DEEP_NAVY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, -1), 2.0, COLOR_ROYAL_GOLD),
                ]
            )
        )
        story.append(wb_banner)
        story.append(Spacer(1, 8))

        # Examiner commentary (why this band, how to reach the next one)
        for label, evaluation in (("Writing", report_data.writing_evaluation), ("Speaking", report_data.speaking_evaluation)):
            summary = getattr(evaluation, "examiner_summary", "") if evaluation else ""
            if summary:
                story.append(Paragraph(f"AI EXAMINER COMMENT — {label.upper()}", styles["section_heading"]))
                story.append(Paragraph(_clean_and_escape(summary), styles["cell_text"]))
                story.append(Spacer(1, 8))

        # Collect Writing & Speaking errors
        combined_errors: list[tuple[str, DetailedError]] = []
        if report_data.writing_evaluation:
            for err in report_data.writing_evaluation.detailed_errors:
                combined_errors.append(("Writing", err))
        if report_data.speaking_evaluation:
            for err in report_data.speaking_evaluation.detailed_errors:
                combined_errors.append(("Speaking", err))

        story.append(
            Paragraph(
                "3. XATOLAR DAFTARI — GRAMMATIK VA LEKSIK XATOLAR TAHLILI (DETAILED ERROR ANALYSIS)",
                styles["section_heading"],
            )
        )

        error_rows: list = [
            [
                Paragraph("#", styles["table_header_center"]),
                Paragraph("Modul", styles["table_header_center"]),
                Paragraph("Xato jumla (Original)", styles["table_header"]),
                Paragraph("To'g'ri shakl (Correction)", styles["table_header"]),
                Paragraph("O'zbekcha izoh va qoida", styles["table_header"]),
            ]
        ]

        if combined_errors:
            for idx, (module_name, err_item) in enumerate(combined_errors, start=1):
                error_rows.append(
                    [
                        Paragraph(str(idx), styles["cell_center_bold"]),
                        Paragraph(_clean_and_escape(module_name), styles["cell_center_bold"]),
                        Paragraph(_clean_and_escape(err_item.original), styles["cell_error_orig"]),
                        Paragraph(_clean_and_escape(err_item.correction), styles["cell_error_fix"]),
                        Paragraph(
                            _clean_and_escape(err_item.explanation_uz),
                            styles["cell_uz_explain"],
                        ),
                    ]
                )
        else:
            error_rows.append(
                [
                    Paragraph("-", styles["cell_center_bold"]),
                    Paragraph("All", styles["cell_center_bold"]),
                    Paragraph("Jiddiy grammatik xatolar aniqlanmadi.", styles["cell_text"]),
                    Paragraph("Yuqori darajadagi akademik tuzilma.", styles["cell_error_fix"]),
                    Paragraph(
                        "Nomzod javoblarida qo'pol grammatik yoki imlo xatolari kuzatilmadi.",
                        styles["cell_uz_explain"],
                    ),
                ]
            )

        error_table = Table(
            error_rows,
            colWidths=[
                usable_width * 0.05,
                usable_width * 0.11,
                usable_width * 0.25,
                usable_width * 0.25,
                usable_width * 0.34,
            ],
            repeatRows=1,
        )
        error_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_DEEP_NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ROW_ALT]),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(error_table)
        story.append(Spacer(1, 10))

        # Collect Band Booster Vocabulary
        combined_vocab: list[tuple[str, BandBoosterVocabulary]] = []
        if report_data.writing_evaluation:
            for voc in report_data.writing_evaluation.band_booster_vocabulary:
                combined_vocab.append(("Writing", voc))
        if report_data.speaking_evaluation:
            for voc in report_data.speaking_evaluation.band_booster_vocabulary:
                combined_vocab.append(("Speaking", voc))

        story.append(
            Paragraph(
                "4. BAND BOOSTER LUG'AT — C1 / BAND 8.0+ DARAJADAGI SINONIMLAR",
                styles["section_heading"],
            )
        )

        vocab_rows: list = [
            [
                Paragraph("#", styles["table_header_center"]),
                Paragraph("Modul", styles["table_header_center"]),
                Paragraph("Ishlatilgan oddiy so'z (Simple)", styles["table_header"]),
                Paragraph(
                    "Tavsiya etilgan C1 / Band 8.0+ muqobil (Advanced)",
                    styles["table_header"],
                ),
            ]
        ]

        if combined_vocab:
            for idx, (module_name, voc_item) in enumerate(combined_vocab, start=1):
                vocab_rows.append(
                    [
                        Paragraph(str(idx), styles["cell_center_bold"]),
                        Paragraph(_clean_and_escape(module_name), styles["cell_center_bold"]),
                        Paragraph(
                            _clean_and_escape(voc_item.simple_used),
                            styles["cell_error_orig"],
                        ),
                        Paragraph(
                            _clean_and_escape(voc_item.advanced_alternative),
                            styles["cell_error_fix"],
                        ),
                    ]
                )
        else:
            vocab_rows.append(
                [
                    Paragraph("1", styles["cell_center_bold"]),
                    Paragraph("General", styles["cell_center_bold"]),
                    Paragraph("very important", styles["cell_error_orig"]),
                    Paragraph("of paramount importance / indispensable", styles["cell_error_fix"]),
                ]
            )

        vocab_table = Table(
            vocab_rows,
            colWidths=[
                usable_width * 0.06,
                usable_width * 0.14,
                usable_width * 0.36,
                usable_width * 0.44,
            ],
            repeatRows=1,
        )
        vocab_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SLATE),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_ROW_ALT]),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(vocab_table)
        story.append(Spacer(1, 10))

        # 5. Speaking Fluency & Pronunciation Diagnostic Recommendations in Uzbek
        s_eval = report_data.speaking_evaluation
        fluency_uz = (
            s_eval.fluency_feedback_uz
            if s_eval and s_eval.fluency_feedback_uz.strip()
            else (
                "Nutq ravonligi (Fluency & Coherence) bo'yicha tavsiya: Gaplar orasida 'Moreover', "
                "'Consequently', 'From my perspective' kabi bog'lovchilardan tabiiy foydalaning va "
                "to'xtalishlarni ('um', 'uh') kamaytiring."
            )
        )
        pronun_uz = (
            s_eval.pronunciation_feedback_uz
            if s_eval and s_eval.pronunciation_feedback_uz.strip()
            else (
                "Talaffuz (Pronunciation) bo'yicha tavsiya: So'z urg'usi (word stress) va gap "
                "intonatsiyasiga e'tibor qarating, murakkab so'zlarni aniq bo'g'inlarga bo'lib talaffuz qiling."
            )
        )

        story.append(
            Paragraph(
                "5. SPEAKING RAVONLIK VA TALAFFUZ BO'YICHA DIAGNOSTIK TAVSIYALAR",
                styles["section_heading"],
            )
        )
        coaching_table = Table(
            [
                [
                    Paragraph("Fluency &amp; Coherence (Nutq ravonligi)", styles["cell_bold"]),
                    Paragraph(_clean_and_escape(fluency_uz), styles["cell_uz_explain"]),
                ],
                [
                    Paragraph("Pronunciation (Talaffuz va intonatsiya)", styles["cell_bold"]),
                    Paragraph(_clean_and_escape(pronun_uz), styles["cell_uz_explain"]),
                ],
            ],
            colWidths=[usable_width * 0.28, usable_width * 0.72],
        )
        coaching_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), COLOR_EMERALD_LIGHT),
                    ("BACKGROUND", (1, 0), (1, -1), COLOR_SOFT_NEUTRAL),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_EMERALD),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(coaching_table)

        return story

    def generate_pdf(
        self,
        report_data: FullExamReportData,
        output_path: str | Path | None = None,
    ) -> bytes:
        """Render the multi-page PDF report into memory, save to disk, and return raw PDF `bytes`."""
        buffer = io.BytesIO()
        left_margin = 28.0
        right_margin = 28.0
        top_margin = 26.0
        bottom_margin = 24.0
        usable_width = A4[0] - left_margin - right_margin

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=left_margin,
            rightMargin=right_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin,
            title=f"IELTS & CEFR Mock AI Report - {report_data.report_id}",
            author="IELTS & CEFR Mock AI",
            subject="Diagnostic IELTS & Uzbekistan Multi-Level CEFR Report",
        )

        styles = _build_styles()
        story: list = []
        story.extend(self._build_page1_elements(report_data, styles, usable_width))
        story.extend(self._build_page2_workbook_elements(report_data, styles, usable_width))

        doc.build(
            story,
            onFirstPage=_draw_page_chrome,
            onLaterPages=_draw_page_chrome,
        )

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Persist to target output path (or default storage/reports/<report_id>.pdf)
        if output_path is not None:
            target_path = Path(output_path)
            if not target_path.is_absolute():
                target_path = BASE_DIR / target_path
        else:
            safe_id = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_"
                for ch in report_data.report_id
            )
            target_path = self.output_dir / f"{safe_id}.pdf"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(pdf_bytes)

        return pdf_bytes

    def generate_and_save(
        self,
        report_data: FullExamReportData,
        output_path: str | Path | None = None,
    ) -> tuple[bytes, Path]:
        """Generate the PDF report and return `(pdf_bytes, saved_file_path)`."""
        if output_path is not None:
            target_path = Path(output_path)
            if not target_path.is_absolute():
                target_path = BASE_DIR / target_path
        else:
            safe_id = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_"
                for ch in report_data.report_id
            )
            target_path = self.output_dir / f"{safe_id}.pdf"

        pdf_bytes = self.generate_pdf(report_data, output_path=target_path)
        return pdf_bytes, target_path


def generate_exam_pdf_report(
    report_data: FullExamReportData,
    output_path: str | Path | None = None,
) -> bytes:
    """Module-level helper to generate a multi-page diagnostic PDF report ($0.00 API cost)."""
    service = PDFReportGeneratorService()
    return service.generate_pdf(report_data=report_data, output_path=output_path)


__all__ = [
    "MANDATORY_LEGAL_DISCLAIMER",
    "PDFReportGeneratorService",
    "band_to_cefr_75_score",
    "build_qr_code_drawing",
    "build_score_progress_bar",
    "generate_exam_pdf_report",
]
