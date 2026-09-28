"""Pydantic v2 schemas for IELTS & Uzbekistan CEFR Multi-level Writing Evaluation.

Enforces the strict JSON output contract required from Anthropic Claude, input
validation for Task 1 and Task 2 submissions (typed text or handwritten images),
and deterministic normalization of scores and CEFR levels.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ExamType = Literal["IELTS", "CEFR"]
CEFRLevel = Literal["BELOW_B1", "B1", "B2", "C1", "C2"]
ImageMediaType = Literal["image/jpeg", "image/png", "image/webp"]


def _normalize_cefr_level(value: Any) -> CEFRLevel:
    """Normalize arbitrary CEFR level strings into canonical literals."""
    if not isinstance(value, str):
        return "BELOW_B1"
    cleaned = value.strip().upper().replace("-", "_").replace(" ", "_")
    if cleaned in {"BELOW_B1", "A1", "A2", "A0", "0", "NONE", "UNCLASSIFIED", "SUB_B1"}:
        return "BELOW_B1"
    if cleaned in {"B1", "B1+", "LEVEL_B1"}:
        return "B1"
    if cleaned in {"B2", "B2+", "LEVEL_B2"}:
        return "B2"
    if cleaned in {"C1", "C1+", "LEVEL_C1"}:
        return "C1"
    if cleaned in {"C2", "LEVEL_C2"}:
        return "C2"
    raise ValueError(
        f"Invalid CEFR level '{value}'. Expected one of: 'BELOW_B1', 'B1', 'B2', 'C1', 'C2'."
    )


class CriteriaScores(BaseModel):
    """Analytical rubric scores across the 4 official assessment criteria."""

    model_config = ConfigDict(extra="forbid")

    task_achievement: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Task Achievement (Task 1) / Task Response (Task 2) score.",
    )
    coherence_cohesion: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Coherence and Cohesion score.",
    )
    lexical_resource: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Lexical Resource (vocabulary range and precision) score.",
    )
    grammatical_range_accuracy: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Grammatical Range and Accuracy score.",
    )

    @field_validator(
        "task_achievement",
        "coherence_cohesion",
        "lexical_resource",
        "grammatical_range_accuracy",
        mode="before",
    )
    @classmethod
    def _validate_finite_float(cls, v: Any) -> float:
        val = float(v)
        if not math.isfinite(val):
            raise ValueError("Criterion score must be a finite number.")
        return round(val, 2)


class DetailedError(BaseModel):
    """Specific grammatical, lexical, or coherence error identified in the essay."""

    model_config = ConfigDict(extra="forbid")

    original: str = Field(
        ...,
        min_length=1,
        description="Exact erroneous phrase or sentence from the student's text.",
    )
    correction: str = Field(
        ...,
        min_length=1,
        description="Corrected academic/natural English version.",
    )
    explanation_uz: str = Field(
        ...,
        min_length=1,
        description="Constructive pedagogical explanation of the error in Uzbek.",
    )


class BandBoosterVocabulary(BaseModel):
    """Lexical upgrade suggestion mapping a basic word used by the student to a C1/Band 8+ alternative."""

    model_config = ConfigDict(extra="forbid")

    simple_used: str = Field(
        ...,
        min_length=1,
        description="Simple or repetitive word/phrase used by the student.",
    )
    advanced_alternative: str = Field(
        ...,
        min_length=1,
        description="High-scoring Band 7.5-9.0 / C1 lexical alternative.",
    )


class WritingEvaluationResult(BaseModel):
    """Strict JSON output contract for IELTS and Uzbekistan Multi-level CEFR Writing evaluation."""

    model_config = ConfigDict(extra="forbid")

    exam_type: ExamType = Field(
        ...,
        description="Target exam format: 'IELTS' (0.0-9.0 Band) or 'CEFR' (Uzbekistan Multi-level).",
    )
    task_1_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Score for Writing Task 1 (1/3 weight).",
    )
    task_2_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Score for Writing Task 2 (2/3 weight).",
    )
    overall_writing_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Weighted overall writing score: (Task1 + Task2 * 2) / 3.",
    )
    cefr_level: CEFRLevel = Field(
        ...,
        description="Mapped CEFR proficiency level ('BELOW_B1', 'B1', 'B2', 'C1', 'C2').",
    )
    criteria_scores: CriteriaScores = Field(
        ...,
        description="Breakdown of scores across the 4 official rubric criteria.",
    )
    detailed_errors: list[DetailedError] = Field(
        default_factory=list,
        description="List of specific errors found in the submission with Uzbek explanations.",
    )
    band_booster_vocabulary: list[BandBoosterVocabulary] = Field(
        default_factory=list,
        description="List of vocabulary upgrade recommendations.",
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

    @field_validator("cefr_level", mode="before")
    @classmethod
    def _validate_cefr_level(cls, v: Any) -> CEFRLevel:
        return _normalize_cefr_level(v)

    @field_validator("task_1_score", "task_2_score", "overall_writing_score", mode="before")
    @classmethod
    def _validate_scores(cls, v: Any) -> float:
        val = float(v)
        if not math.isfinite(val):
            raise ValueError("Score must be a finite float.")
        return round(val, 2)

    @model_validator(mode="after")
    def _validate_exam_score_bounds(self) -> WritingEvaluationResult:
        """Ensure IELTS scores never exceed 9.0 Band."""
        if self.exam_type == "IELTS":
            for field_name in ("task_1_score", "task_2_score", "overall_writing_score"):
                val = getattr(self, field_name)
                if val > 9.0:
                    raise ValueError(
                        f"IELTS {field_name} cannot exceed 9.0 (got {val})."
                    )
            for crit_name in (
                "task_achievement",
                "coherence_cohesion",
                "lexical_resource",
                "grammatical_range_accuracy",
            ):
                c_val = getattr(self.criteria_scores, crit_name)
                if c_val > 9.0:
                    raise ValueError(
                        f"IELTS criteria_scores.{crit_name} cannot exceed 9.0 (got {c_val})."
                    )
        return self


class WritingTaskInput(BaseModel):
    """Input payload for a single Writing Task (Task 1 or Task 2)."""

    model_config = ConfigDict(extra="forbid")

    task_number: Literal[1, 2] = Field(
        default=1,
        description="Task number: 1 (Report/Letter, ~150 words) or 2 (Essay, ~250 words).",
    )
    prompt_topic: str = Field(
        ...,
        min_length=3,
        description="The exam question/topic prompt assigned to the candidate.",
    )
    student_text: str | None = Field(
        default=None,
        description="Candidate's typed or OCR-transcribed response text.",
    )
    image_bytes: bytes | None = Field(
        default=None,
        exclude=True,
        description="Optional raw image bytes of a handwritten essay for Vision OCR.",
    )
    image_base64: str | None = Field(
        default=None,
        exclude=True,
        description="Optional base64-encoded image string of a handwritten essay.",
    )
    image_url: str | None = Field(
        default=None,
        description="Optional URL or local path to a handwritten essay image.",
    )
    image_media_type: ImageMediaType = Field(
        default="image/jpeg",
        description="MIME type of the handwritten image ('image/jpeg', 'image/png', 'image/webp').",
    )

    @property
    def word_count(self) -> int:
        """Calculate the word count of the student's text."""
        if not self.student_text or not self.student_text.strip():
            return 0
        return len(self.student_text.strip().split())

    @property
    def has_image(self) -> bool:
        """Return True if an image source is provided for Vision OCR."""
        return bool(self.image_bytes or self.image_base64 or self.image_url)


class WritingEvaluationRequest(BaseModel):
    """Full request payload for evaluating Task 1 and Task 2 Writing submissions."""

    model_config = ConfigDict(extra="ignore")

    exam_type: ExamType = Field(
        default="IELTS",
        description="Exam format: 'IELTS' or 'CEFR'.",
    )
    task_1: WritingTaskInput = Field(
        ...,
        description="Task 1 submission (Chart/Graph/Process for IELTS Academic, Letter for GT/CEFR).",
    )
    task_2: WritingTaskInput = Field(
        ...,
        description="Task 2 submission (Academic/Opinion/Discussion Essay).",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_flat_inputs(cls, data: Any) -> Any:
        """Allow constructing WritingEvaluationRequest from either nested task_1/task_2 or flat fields."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "task_1" not in out and (
            "task_1_text" in out or "task_1_prompt" in out or "task_1_image_bytes" in out
        ):
            out["task_1"] = {
                "task_number": 1,
                "prompt_topic": out.pop("task_1_prompt", "Writing Task 1 Prompt"),
                "student_text": out.pop("task_1_text", None),
                "image_bytes": out.pop("task_1_image_bytes", None),
                "image_base64": out.pop("task_1_image_base64", None),
                "image_url": out.pop("task_1_image_url", None),
            }
        if "task_2" not in out and (
            "task_2_text" in out or "task_2_prompt" in out or "task_2_image_bytes" in out
        ):
            out["task_2"] = {
                "task_number": 2,
                "prompt_topic": out.pop("task_2_prompt", "Writing Task 2 Prompt"),
                "student_text": out.pop("task_2_text", None),
                "image_bytes": out.pop("task_2_image_bytes", None),
                "image_base64": out.pop("task_2_image_base64", None),
                "image_url": out.pop("task_2_image_url", None),
            }
        return out


class VisionOCRResult(BaseModel):
    """Output from the Vision OCR transcription pipeline for handwritten essays."""

    model_config = ConfigDict(extra="forbid")

    transcribed_text: str = Field(
        ...,
        description="Verbatim transcription of the student's handwritten text preserving errors.",
    )
    word_count: int = Field(
        ...,
        ge=0,
        description="Total word count of the transcribed text.",
    )
    provider: Literal["claude", "openai"] = Field(
        ...,
        description="Vision provider that performed the OCR.",
    )
    model: str = Field(
        ...,
        description="Specific Vision model used.",
    )


# Backward-compatible aliases
DetailedErrorItem = DetailedError
BandBoosterItem = BandBoosterVocabulary
