"""Pydantic v2 schemas for Full 4-Skill Exam Aggregation and PDF Report Generation.

Defines:
- `SectionScoreSummary`: Dual-scale score aggregation across Listening, Reading,
  Writing, and Speaking for both official IELTS (0.0 - 9.0 Band) and Uzbekistan
  National BBA Multi-level CEFR (0 - 75 Standard Score).
- `FullExamReportData`: Complete payload consumed by `PDFReportGeneratorService`
  to render the multi-page Diagnostic Certificate & Error Workbook PDF.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings
from app.schemas.speaking import SpeakingEvaluationResult
from app.schemas.writing import (
    CEFRLevel,
    ExamType,
    WritingEvaluationResult,
    _normalize_cefr_level,
)
def round_to_half_band(score: float) -> float:
    """Round a score to the nearest 0.5 increment within [0.0, 9.0]."""
    clamped = max(0.0, min(9.0, float(score)))
    return round(clamped * 2.0) / 2.0


def round_ielts_overall_band(*scores: float) -> float:
    """Apply official IELTS 0.25 / 0.75 overall band rounding rule."""
    if not scores:
        return 0.0
    avg = sum(float(s) for s in scores) / len(scores)
    clamped = max(0.0, min(9.0, avg))
    integer_part = int(clamped)
    fraction = round(clamped - integer_part, 6)
    if fraction < 0.25:
        return float(integer_part)
    if fraction < 0.75:
        return float(integer_part) + 0.5
    return min(9.0, float(integer_part + 1))


def map_ielts_band_to_cefr_level(band: float) -> CEFRLevel:
    """Map an IELTS Band (0.0-9.0) to CEFR level."""
    if band >= 8.5:
        return "C2"
    if band >= 7.0:
        return "C1"
    if band >= 5.5:
        return "B2"
    if band >= 4.0:
        return "B1"
    return "BELOW_B1"


def map_cefr_score_to_level(score_75: float) -> CEFRLevel:
    """Map an Uzbekistan BBA 0-75 standard score to CEFR level."""
    if score_75 >= 65.0:
        return "C1"
    if score_75 >= 51.0:
        return "B2"
    if score_75 >= 38.0:
        return "B1"
    return "BELOW_B1"


def band_to_cefr_75_score(band_score: float) -> float:
    """Convert an IELTS 0.0 - 9.0 Band score into the Uzbekistan BBA 0.0 - 75.0 scale.

    Anchors align with Uzbekistan Multi-level psychometric thresholds:
    - Band 9.0 -> 75.0 (C1 max)
    - Band 7.5 -> 68.0 (C1 solid)
    - Band 7.0 -> 65.0 (C1 threshold)
    - Band 6.5 -> 60.0 (B2 high)
    - Band 6.0 -> 55.0 (B2 solid)
    - Band 5.5 -> 51.0 (B2 threshold)
    - Band 5.0 -> 46.0 (B1 high)
    - Band 4.5 -> 42.0 (B1 solid)
    - Band 4.0 -> 38.0 (B1 threshold)
    """
    val = max(0.0, min(9.0, float(band_score)))
    if val <= 0.0:
        return 0.0

    anchor_table: dict[float, float] = {
        9.0: 75.0,
        8.5: 73.0,
        8.0: 70.0,
        7.5: 68.0,
        7.0: 65.0,
        6.5: 60.0,
        6.0: 55.0,
        5.5: 51.0,
        5.0: 46.0,
        4.5: 42.0,
        4.0: 38.0,
        3.5: 32.0,
        3.0: 26.0,
        2.5: 20.0,
        2.0: 15.0,
        1.5: 10.0,
        1.0: 6.0,
        0.5: 3.0,
        0.0: 0.0,
    }
    half_band = round_to_half_band(val)
    if half_band in anchor_table:
        return anchor_table[half_band]
    return round(min(75.0, (val / 9.0) * 75.0), 1)


class SectionScoreSummary(BaseModel):
    """Dual-scale 4-skill score summary (IELTS 0.0-9.0 Band & Uzbekistan BBA 0-75 Scale)."""

    model_config = ConfigDict(extra="forbid")

    listening_raw: int = Field(
        default=0,
        ge=0,
        le=40,
        description="Raw correct answers in Listening (0 - 40).",
    )
    listening_band: float = Field(
        default=0.0,
        ge=0.0,
        le=9.0,
        description="Listening score on the official IELTS 0.0 - 9.0 Band scale.",
    )
    listening_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Listening score on the Uzbekistan BBA 0.0 - 75.0 scale.",
    )

    reading_raw: int = Field(
        default=0,
        ge=0,
        le=40,
        description="Raw correct answers in Reading (0 - 40).",
    )
    reading_band: float = Field(
        default=0.0,
        ge=0.0,
        le=9.0,
        description="Reading score on the official IELTS 0.0 - 9.0 Band scale.",
    )
    reading_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Reading score on the Uzbekistan BBA 0.0 - 75.0 scale.",
    )

    writing_band: float = Field(
        default=0.0,
        ge=0.0,
        le=9.0,
        description="Writing score on the official IELTS 0.0 - 9.0 Band scale.",
    )
    writing_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Writing score on the Uzbekistan BBA 0.0 - 75.0 scale.",
    )

    speaking_band: float = Field(
        default=0.0,
        ge=0.0,
        le=9.0,
        description="Speaking score on the official IELTS 0.0 - 9.0 Band scale.",
    )
    speaking_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Speaking score on the Uzbekistan BBA 0.0 - 75.0 scale.",
    )

    overall_band: float = Field(
        default=0.0,
        ge=0.0,
        le=9.0,
        description="Overall 4-skill IELTS Band rounded via the official .25 / .75 rule.",
    )
    overall_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Overall Uzbekistan BBA Multi-level standard score (0.0 - 75.0).",
    )
    cefr_level: Literal["BELOW_B1", "B1", "B2", "C1", "C2"] = Field(
        default="BELOW_B1",
        description="Resolved CEFR proficiency level ('BELOW_B1', 'B1', 'B2', 'C1', 'C2').",
    )

    @field_validator("cefr_level", mode="before")
    @classmethod
    def _validate_cefr(cls, v: Any) -> CEFRLevel:
        return _normalize_cefr_level(v)

    @model_validator(mode="after")
    def _populate_derived_scores(self) -> SectionScoreSummary:
        """Auto-derive 0-75 scores, overall band (.25/.75 rule), and CEFR level when omitted."""
        if self.listening_score_75 == 0.0 and self.listening_band > 0.0:
            self.listening_score_75 = band_to_cefr_75_score(self.listening_band)
        if self.reading_score_75 == 0.0 and self.reading_band > 0.0:
            self.reading_score_75 = band_to_cefr_75_score(self.reading_band)
        if self.writing_score_75 == 0.0 and self.writing_band > 0.0:
            self.writing_score_75 = band_to_cefr_75_score(self.writing_band)
        if self.speaking_score_75 == 0.0 and self.speaking_band > 0.0:
            self.speaking_score_75 = band_to_cefr_75_score(self.speaking_band)

        skill_bands = [
            self.listening_band,
            self.reading_band,
            self.writing_band,
            self.speaking_band,
        ]
        if self.overall_band == 0.0 and any(b > 0.0 for b in skill_bands):
            self.overall_band = round_ielts_overall_band(skill_bands)

        skill_75 = [
            self.listening_score_75,
            self.reading_score_75,
            self.writing_score_75,
            self.speaking_score_75,
        ]
        if self.overall_score_75 == 0.0 and any(s > 0.0 for s in skill_75):
            self.overall_score_75 = round(sum(skill_75) / 4.0, 1)

        if self.cefr_level == "BELOW_B1":
            if self.overall_band >= 4.0:
                self.cefr_level = map_ielts_band_to_cefr_level(self.overall_band)
            elif self.overall_score_75 >= 38.0:
                self.cefr_level = map_cefr_score_to_level(self.overall_score_75)

        return self


class FullExamReportData(BaseModel):
    """Complete data payload for generating the multi-page IELTS & CEFR Mock AI PDF Report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(
        default="MOCK-2026-0001",
        min_length=3,
        description="Unique diagnostic report identifier (e.g., 'MOCK-2026-0001').",
    )
    candidate_name: str = Field(
        default="Candidate",
        min_length=1,
        description="Full name or Telegram display name of the candidate.",
    )
    candidate_telegram_id: int | None = Field(
        default=None,
        description="Optional Telegram numeric user ID.",
    )
    exam_type: Literal["IELTS", "CEFR"] = Field(
        default="IELTS",
        description="Target exam format: 'IELTS' (Academic/GT) or 'CEFR' (Uzbekistan BBA Multi-level).",
    )
    exam_date: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        description="ISO or formatted date of the mock examination.",
    )
    verification_url: str = Field(
        default="https://t.me/ielts_cefr_mock_ai_bot",
        description="URL encoded into the certificate verification QR code.",
    )
    scores: SectionScoreSummary = Field(
        default_factory=SectionScoreSummary,
        description="Aggregated 4-skill and overall dual-scale scores.",
    )
    writing_evaluation: WritingEvaluationResult | None = Field(
        default=None,
        description="Detailed AI Writing evaluation (criteria scores, errors, vocabulary).",
    )
    speaking_evaluation: SpeakingEvaluationResult | None = Field(
        default=None,
        description="Detailed AI Speaking evaluation (criteria scores, fluency/pronunciation notes, errors).",
    )
    disclaimer_text: str = Field(
        default_factory=lambda: settings.PDF_DISCLAIMER_TEXT,
        description="Mandatory legal disclaimer printed in the certificate footer.",
    )

    @field_validator("exam_type", mode="before")
    @classmethod
    def _normalize_exam_type(cls, v: Any) -> ExamType:
        if isinstance(v, str):
            upper = v.strip().upper()
            if upper in {"IELTS", "IELTS_ACADEMIC", "IELTS_GENERAL"}:
                return "IELTS"
            if upper in {"CEFR", "MULTILEVEL", "MULTI_LEVEL", "MULTI-LEVEL", "BBA"}:
                return "CEFR"
        raise ValueError(f"Invalid exam_type '{v}'. Expected 'IELTS' or 'CEFR'.")
