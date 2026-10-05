"""Pydantic v2 schemas for IELTS & Uzbekistan CEFR Multi-level Speaking Evaluation.

Defines:
- `SpeakingCriteriaScores`: 4 official Speaking criteria (Fluency & Coherence,
  Lexical Resource, Grammatical Range & Accuracy, Pronunciation).
- `AudioTranscriptionResult`: OpenAI Whisper (`whisper-1`) STT output with speech
  rate (WPM) and hesitation/filler word telemetry.
- `SpeakingPartInput` & `SpeakingEvaluationRequest`: Input payloads for Speaking
  Part 1 (Interview), Part 2 (Long Turn / Cue Card), and Part 3 (Discussion).
- `SpeakingEvaluationResult`: Strict JSON output contract from Anthropic Claude
  with dual-scale scoring (IELTS 0.0-9.0 Band & Uzbekistan BBA 0-75 Standard Score),
  Uzbek fluency/pronunciation coaching, detailed error analysis, and C1/Band 8+
  vocabulary boosters.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.writing import (
    BandBoosterVocabulary,
    CEFRLevel,
    DetailedError,
    ExamType,
    _normalize_cefr_level,
)

SpeakingPartNumber = Literal[1, 2, 3]
AudioMimeType = Literal[
    "audio/ogg",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
]


class SpeakingCriteriaScores(BaseModel):
    """Analytical rubric scores across the 4 official Speaking assessment criteria."""

    model_config = ConfigDict(extra="forbid")

    fluency_coherence: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Fluency and Coherence (speech rate, logical connectors, minimal hesitation).",
    )
    lexical_resource: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Lexical Resource (idiomatic language, collocations, paraphrasing).",
    )
    grammatical_range_accuracy: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Grammatical Range and Accuracy (complex structures, error-free clauses).",
    )
    pronunciation: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Pronunciation (intelligibility, stress, intonation, clarity).",
    )

    @field_validator(
        "fluency_coherence",
        "lexical_resource",
        "grammatical_range_accuracy",
        "pronunciation",
        mode="before",
    )
    @classmethod
    def _validate_finite_float(cls, v: Any) -> float:
        val = float(v)
        if not math.isfinite(val):
            raise ValueError("Speaking criterion score must be a finite number.")
        return round(val, 2)


class AudioTranscriptionResult(BaseModel):
    """Output from OpenAI Whisper (`whisper-1`) STT pipeline with speech telemetry."""

    model_config = ConfigDict(extra="forbid")

    part_number: SpeakingPartNumber = Field(
        default=1,
        description="Speaking part number (1, 2, or 3).",
    )
    transcribed_text: str = Field(
        ...,
        description="Verbatim transcript produced by OpenAI Whisper STT.",
    )
    word_count: int = Field(
        ...,
        ge=0,
        description="Total word count of the transcribed speech.",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Audio duration in seconds (if known).",
    )
    words_per_minute: float = Field(
        default=0.0,
        ge=0.0,
        description="Calculated speech rate in Words Per Minute (WPM).",
    )
    filler_word_count: int = Field(
        default=0,
        ge=0,
        description="Count of hesitation markers and filler words (um, uh, er, like, you know).",
    )
    filler_words_detected: list[str] = Field(
        default_factory=list,
        description="List of specific filler words/phrases found in the transcript.",
    )
    model: str = Field(
        default="whisper-1",
        description="STT model used for transcription.",
    )


class SpeakingPartInput(BaseModel):
    """Input payload for a single Speaking Part (Part 1, Part 2, or Part 3)."""

    model_config = ConfigDict(extra="forbid")

    part_number: SpeakingPartNumber = Field(
        default=1,
        description="Speaking part: 1 (Introduction/Interview), 2 (Cue Card Long Turn), 3 (Two-way Discussion).",
    )
    question_prompt: str = Field(
        ...,
        min_length=3,
        description="Examiner question(s) or Part 2 Cue Card topic assigned to the candidate.",
    )
    transcript_text: str | None = Field(
        default=None,
        description="Candidate's spoken response transcript (if already transcribed).",
    )
    audio_bytes: bytes | None = Field(
        default=None,
        exclude=True,
        description="Raw audio bytes (.ogg, .mp3, .wav, .m4a) for Whisper STT transcription.",
    )
    audio_path_or_url: str | None = Field(
        default=None,
        description="Local filesystem path or Cloudflare R2 URL to the candidate's voice recording.",
    )
    audio_filename: str = Field(
        default="voice.ogg",
        description="Filename with extension used by Whisper to infer container format (.ogg, .mp3, .wav).",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration of the voice recording in seconds.",
    )

    @property
    def word_count(self) -> int:
        """Return word count of `transcript_text`."""
        if not self.transcript_text or not self.transcript_text.strip():
            return 0
        return len(self.transcript_text.strip().split())

    @property
    def has_audio(self) -> bool:
        """Return True if raw audio bytes or an audio file path/URL is provided."""
        return bool(self.audio_bytes or self.audio_path_or_url)


class SpeakingEvaluationRequest(BaseModel):
    """Full request payload for evaluating a 3-part IELTS or CEFR Speaking test."""

    model_config = ConfigDict(extra="ignore")

    exam_type: ExamType = Field(
        default="IELTS",
        description="Exam format: 'IELTS' (0.0-9.0 Band) or 'CEFR' (Uzbekistan Multi-level 0-75).",
    )
    part_1: SpeakingPartInput = Field(
        ...,
        description="Part 1: Introduction and interview on familiar topics (4-5 minutes).",
    )
    part_2: SpeakingPartInput = Field(
        ...,
        description="Part 2: Individual long turn / Cue Card monologue (1-2 minutes).",
    )
    part_3: SpeakingPartInput = Field(
        ...,
        description="Part 3: Two-way abstract discussion linked to Part 2 topic (4-5 minutes).",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_flat_inputs(cls, data: Any) -> Any:
        """Allow constructing SpeakingEvaluationRequest from either nested part_1..3 or flat fields."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for part_num in (1, 2, 3):
            key = f"part_{part_num}"
            if key not in out and (
                f"{key}_text" in out
                or f"{key}_prompt" in out
                or f"{key}_audio_bytes" in out
                or f"{key}_audio_url" in out
            ):
                out[key] = {
                    "part_number": part_num,
                    "question_prompt": out.pop(
                        f"{key}_prompt", f"Speaking Part {part_num} Prompt"
                    ),
                    "transcript_text": out.pop(f"{key}_text", None),
                    "audio_bytes": out.pop(f"{key}_audio_bytes", None),
                    "audio_path_or_url": out.pop(f"{key}_audio_url", None),
                    "audio_filename": out.pop(f"{key}_filename", f"part_{part_num}.ogg"),
                    "duration_seconds": out.pop(f"{key}_duration_seconds", 0.0),
                }
        return out


class SpeakingEvaluationResult(BaseModel):
    """Strict JSON output contract for IELTS and Uzbekistan Multi-level CEFR Speaking evaluation."""

    model_config = ConfigDict(extra="forbid")

    exam_type: ExamType = Field(
        ...,
        description="Target exam format: 'IELTS' or 'CEFR'.",
    )
    part_1_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Score for Speaking Part 1 (Interview).",
    )
    part_2_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Score for Speaking Part 2 (Cue Card Long Turn).",
    )
    part_3_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Score for Speaking Part 3 (Abstract Discussion).",
    )
    overall_speaking_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Overall Speaking Band score (0.0 - 9.0 in 0.5 increments).",
    )
    standard_score_75: float = Field(
        default=0.0,
        ge=0.0,
        le=75.0,
        description="Uzbekistan BBA Multi-level standard score on the 0.0 - 75.0 scale.",
    )
    cefr_level: CEFRLevel = Field(
        ...,
        description="Mapped CEFR proficiency level ('BELOW_B1', 'B1', 'B2', 'C1', 'C2').",
    )
    criteria_scores: SpeakingCriteriaScores = Field(
        ...,
        description="Breakdown across the 4 official Speaking criteria.",
    )
    fluency_feedback_uz: str = Field(
        default="",
        description="Actionable coaching feedback on Fluency, Coherence, and speech rate in Uzbek.",
    )
    pronunciation_feedback_uz: str = Field(
        default="",
        description="Actionable coaching feedback on Pronunciation, intonation, and clarity in Uzbek.",
    )
    detailed_errors: list[DetailedError] = Field(
        default_factory=list,
        description="Spoken grammar, lexical, or register errors with Uzbek explanations.",
    )
    band_booster_vocabulary: list[BandBoosterVocabulary] = Field(
        default_factory=list,
        description="Idiomatic and C1/Band 8+ spoken vocabulary upgrade suggestions.",
    )
    examiner_summary: str = Field(
        default="",
        max_length=3000,
        description="Short examiner commentary: overall performance and concrete steps to reach the next band.",
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

    @field_validator(
        "part_1_score",
        "part_2_score",
        "part_3_score",
        "overall_speaking_score",
        "standard_score_75",
        mode="before",
    )
    @classmethod
    def _validate_scores(cls, v: Any) -> float:
        val = float(v)
        if not math.isfinite(val):
            raise ValueError("Speaking score must be a finite float.")
        return round(val, 2)

    @model_validator(mode="after")
    def _validate_and_sync_scales(self) -> SpeakingEvaluationResult:
        """Ensure IELTS band scores stay within [0.0, 9.0] and auto-derive `standard_score_75` if omitted."""
        if self.exam_type == "IELTS":
            for field_name in (
                "part_1_score",
                "part_2_score",
                "part_3_score",
                "overall_speaking_score",
            ):
                val = getattr(self, field_name)
                if val > 9.0:
                    raise ValueError(
                        f"IELTS {field_name} cannot exceed 9.0 (got {val})."
                    )
            for crit_name in (
                "fluency_coherence",
                "lexical_resource",
                "grammatical_range_accuracy",
                "pronunciation",
            ):
                c_val = getattr(self.criteria_scores, crit_name)
                if c_val > 9.0:
                    raise ValueError(
                        f"IELTS criteria_scores.{crit_name} cannot exceed 9.0 (got {c_val})."
                    )

        if self.standard_score_75 == 0.0 and self.overall_speaking_score > 0.0:
            if self.overall_speaking_score <= 9.0:
                self.standard_score_75 = round(
                    min(75.0, (self.overall_speaking_score / 9.0) * 75.0), 1
                )
            else:
                self.standard_score_75 = round(min(75.0, self.overall_speaking_score), 1)
        return self
