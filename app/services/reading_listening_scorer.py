"""Deterministic ($0.00 Zero-Token) Scorer for IELTS & Uzbekistan Multi-Level CEFR.

Provides:
1. Official IELTS 40-question Listening & Reading (Academic / General Training)
   raw-to-band conversion tables.
2. Official IELTS 4-skill overall band rounding (`round_ielts_overall_band`:
   decimal < 0.25 -> .0, 0.25 <= decimal < 0.75 -> .5, decimal >= 0.75 -> next .0).
3. Official Writing Task 1 (1/3 weight) + Task 2 (2/3 weight) weighted score calculator.
4. Uzbekistan National CEFR / Multi-Level (BBA) 0-75 standard score calculation
   and B1 / B2 / C1 level mapping.
5. Zero-token objective answer-key grader with case-insensitive & multi-variant matching.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.writing import CEFRLevel, ExamType

SkillSection = Literal["listening", "reading"]
ReadingModule = Literal["academic", "general"]

# =====================================================================
# 1. OFFICIAL IELTS 40-QUESTION RAW-TO-BAND CONVERSION TABLES
# =====================================================================

IELTS_LISTENING_BAND_TABLE: dict[int, float] = {
    40: 9.0,
    39: 9.0,
    38: 8.5,
    37: 8.5,
    36: 8.0,
    35: 8.0,
    34: 7.5,
    33: 7.5,
    32: 7.5,
    31: 7.0,
    30: 7.0,
    29: 6.5,
    28: 6.5,
    27: 6.5,
    26: 6.5,
    25: 6.0,
    24: 6.0,
    23: 6.0,
    22: 5.5,
    21: 5.5,
    20: 5.5,
    19: 5.5,
    18: 5.5,
    17: 5.0,
    16: 5.0,
    15: 4.5,
    14: 4.5,
    13: 4.5,
    12: 4.0,
    11: 4.0,
    10: 4.0,
    9: 3.5,
    8: 3.5,
    7: 3.0,
    6: 3.0,
    5: 2.5,
    4: 2.5,
    3: 2.0,
    2: 2.0,
    1: 1.0,
    0: 0.0,
}

IELTS_ACADEMIC_READING_BAND_TABLE: dict[int, float] = {
    40: 9.0,
    39: 9.0,
    38: 8.5,
    37: 8.5,
    36: 8.0,
    35: 8.0,
    34: 7.5,
    33: 7.5,
    32: 7.0,
    31: 7.0,
    30: 7.0,
    29: 6.5,
    28: 6.5,
    27: 6.5,
    26: 6.0,
    25: 6.0,
    24: 6.0,
    23: 6.0,
    22: 5.5,
    21: 5.5,
    20: 5.5,
    19: 5.5,
    18: 5.0,
    17: 5.0,
    16: 5.0,
    15: 5.0,
    14: 4.5,
    13: 4.5,
    12: 4.0,
    11: 4.0,
    10: 4.0,
    9: 3.5,
    8: 3.5,
    7: 3.0,
    6: 3.0,
    5: 2.5,
    4: 2.5,
    3: 2.0,
    2: 2.0,
    1: 1.0,
    0: 0.0,
}

IELTS_GENERAL_READING_BAND_TABLE: dict[int, float] = {
    40: 9.0,
    39: 8.5,
    38: 8.0,
    37: 8.0,
    36: 7.5,
    35: 7.0,
    34: 7.0,
    33: 6.5,
    32: 6.5,
    31: 6.0,
    30: 6.0,
    29: 5.5,
    28: 5.5,
    27: 5.5,
    26: 5.0,
    25: 5.0,
    24: 5.0,
    23: 5.0,
    22: 4.5,
    21: 4.5,
    20: 4.5,
    19: 4.5,
    18: 4.0,
    17: 4.0,
    16: 4.0,
    15: 4.0,
    14: 3.5,
    13: 3.5,
    12: 3.5,
    11: 3.0,
    10: 3.0,
    9: 3.0,
    8: 2.5,
    7: 2.5,
    6: 2.5,
    5: 2.0,
    4: 2.0,
    3: 2.0,
    2: 1.0,
    1: 1.0,
    0: 0.0,
}


# =====================================================================
# 2. DETERMINISTIC ROUNDING & CONVERSION FUNCTIONS
# =====================================================================


def round_to_half_band(score: float) -> float:
    """Round a raw IELTS score to the nearest 0.5 band increment using official rules.

    Official IELTS rounding rule:
    - Fractional part < 0.25          -> rounds down to .0
    - 0.25 <= Fractional part < 0.75  -> rounds to .5
    - Fractional part >= 0.75         -> rounds up to next .0
    Clamped strictly within [0.0, 9.0].
    """
    val = float(score)
    if not math.isfinite(val) or val <= 0.0:
        return 0.0
    if val >= 9.0:
        return 9.0

    clean = round(val, 6)
    whole = math.floor(clean)
    fraction = round(clean - whole, 6)

    if fraction < 0.25:
        result = float(whole)
    elif fraction < 0.75:
        result = float(whole) + 0.5
    else:
        result = float(whole) + 1.0

    return min(9.0, max(0.0, result))


def round_ielts_overall_band(
    *scores: float | Iterable[float],
    listening: float | None = None,
    reading: float | None = None,
    writing: float | None = None,
    speaking: float | None = None,
) -> float:
    """Calculate and round the official IELTS Overall Band Score.

    Supports flexible invocation:
    1. Four individual skill bands: `round_ielts_overall_band(6.5, 6.5, 6.0, 6.0)` -> `6.5`
    2. Keyword skill bands: `round_ielts_overall_band(listening=6.5, reading=6.5, writing=6.0, speaking=6.0)` -> `6.5`
    3. Sequence of skill bands: `round_ielts_overall_band([6.5, 6.5, 6.0, 6.0])` -> `6.5`
    4. Pre-averaged raw float: `round_ielts_overall_band(6.25)` -> `6.5`, `round_ielts_overall_band(6.75)` -> `7.0`
    """
    collected: list[float] = []

    for kw_val in (listening, reading, writing, speaking):
        if kw_val is not None:
            collected.append(float(kw_val))

    for item in scores:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            collected.extend(float(x) for x in item)
        else:
            collected.append(float(item))

    if not collected:
        raise ValueError("At least one score must be provided to round_ielts_overall_band.")

    avg_score = sum(collected) / len(collected)
    return round_to_half_band(avg_score)


def calculate_weighted_writing_score(
    task_1_score: float,
    task_2_score: float,
    exam_type: ExamType = "IELTS",
) -> float:
    """Calculate the weighted overall Writing score where Task 1 = 1/3 and Task 2 = 2/3.

    Formula: `raw_overall = (task_1_score + (task_2_score * 2.0)) / 3.0`
    - For IELTS (or 0.0-9.0 scale): rounds to the nearest 0.5 band increment.
    - For CEFR on the 0-75 standard scale (scores > 9.0): rounds to 1 decimal place, clamped to [0.0, 75.0].
    """
    t1 = max(0.0, float(task_1_score))
    t2 = max(0.0, float(task_2_score))
    raw_overall = (t1 + (t2 * 2.0)) / 3.0

    if exam_type == "CEFR" and (t1 > 9.0 or t2 > 9.0):
        return min(75.0, max(0.0, round(raw_overall, 1)))

    return round_to_half_band(raw_overall)


def map_ielts_band_to_cefr_level(band_score: float) -> CEFRLevel:
    """Map an IELTS Band score (0.0 - 9.0) to its Uzbekistan BBA / CEFR level equivalent.

    Mapping rules from SKILL.md:
    - 7.0 - 9.0 -> C1
    - 5.5 - 6.5 -> B2
    - 4.0 - 5.0 -> B1
    - < 4.0     -> BELOW_B1
    """
    val = float(band_score)
    if val >= 7.0:
        return "C1"
    if val >= 5.5:
        return "B2"
    if val >= 4.0:
        return "B1"
    return "BELOW_B1"


def map_cefr_score_to_level(standard_score: float) -> CEFRLevel:
    """Map an Uzbekistan Multi-level 0-75 standard score to its official CEFR level.

    Mapping rules from SKILL.md:
    - 65 - 75 points -> C1
    - 51 - 64 points -> B2
    - 38 - 50 points -> B1
    - 0  - 37 points -> BELOW_B1
    """
    val = float(standard_score)
    if val >= 65.0:
        return "C1"
    if val >= 51.0:
        return "B2"
    if val >= 38.0:
        return "B1"
    return "BELOW_B1"


def resolve_cefr_level(score: float, exam_type: ExamType = "IELTS") -> CEFRLevel:
    """Deterministically resolve the CEFR level for either an IELTS Band (0-9) or CEFR score (0-75)."""
    val = float(score)
    if exam_type == "CEFR" and val > 9.0:
        return map_cefr_score_to_level(val)
    return map_ielts_band_to_cefr_level(val)


def convert_listening_raw_to_band(correct_count: int) -> float:
    """Convert raw correct answers (0-40) in IELTS Listening to an official Band score."""
    clamped = max(0, min(40, int(correct_count)))
    return IELTS_LISTENING_BAND_TABLE[clamped]


def convert_reading_raw_to_band(
    correct_count: int,
    module: ReadingModule = "academic",
) -> float:
    """Convert raw correct answers (0-40) in IELTS Reading (Academic or General) to a Band score."""
    clamped = max(0, min(40, int(correct_count)))
    if module.lower().strip() == "general":
        return IELTS_GENERAL_READING_BAND_TABLE[clamped]
    return IELTS_ACADEMIC_READING_BAND_TABLE[clamped]


def convert_raw_to_cefr_standard_score(
    correct_count: int,
    total_questions: int = 40,
) -> float:
    """Convert raw correct answers into the Uzbekistan Multi-level 0-75 standard score scale."""
    if total_questions <= 0:
        raise ValueError("total_questions must be greater than 0.")
    clamped = max(0, min(total_questions, int(correct_count)))
    raw_75 = (clamped / float(total_questions)) * 75.0
    return round(min(75.0, max(0.0, raw_75)), 1)


# =====================================================================
# 3. ZERO-TOKEN ($0.00) OBJECTIVE ANSWER GRADING MODELS & SERVICE
# =====================================================================

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_objective_answer(answer: Any) -> str:
    """Normalize a student or answer-key response for deterministic matching.

    - Lowercases text
    - Collapses internal whitespace
    - Strips surrounding whitespace and non-essential punctuation (quotes, trailing dots)
    """
    if answer is None:
        return ""
    text = str(answer).strip().lower()
    text = text.strip("\"'`.,;:")
    text = _WHITESPACE_RE.sub(" ", text)
    return text


def is_objective_answer_correct(
    user_answer: Any,
    expected_answer: str | Sequence[str],
) -> bool:
    """Check if `user_answer` matches `expected_answer` (supporting `/` or `|` or list variants)."""
    norm_user = normalize_objective_answer(user_answer)
    if not norm_user:
        return False

    if isinstance(expected_answer, str):
        # Split alternatives by '|' or '/' if present (e.g., "colour / color" or "19 | nineteen")
        variants = [
            normalize_objective_answer(part)
            for part in re.split(r"[|/]", expected_answer)
            if normalize_objective_answer(part)
        ]
        if not variants:
            variants = [normalize_objective_answer(expected_answer)]
    else:
        variants = [
            normalize_objective_answer(item)
            for item in expected_answer
            if normalize_objective_answer(item)
        ]

    if norm_user in variants:
        return True
    # Numbers (phone numbers, prices) are often typed with spaces or hyphens: "07894 32109".
    # Numbers and codes (phone numbers, postcodes) are often typed with spaces or hyphens.
    compact_user = re.sub(r"[\s\-]", "", norm_user)
    coded = {re.sub(r"[\s\-]", "", v) for v in variants if any(ch.isdigit() for ch in v)}
    return compact_user in coded


class ObjectiveQuestionResult(BaseModel):
    """Per-question grading breakdown for Listening and Reading."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    user_answer: str
    correct_answer: str
    is_correct: bool


class ObjectiveSectionScoreResult(BaseModel):
    """Complete deterministic grading output for a Listening or Reading test section."""

    model_config = ConfigDict(extra="forbid")

    section: SkillSection
    exam_type: ExamType
    reading_module: ReadingModule = Field(default="academic")
    correct_count: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)
    accuracy_percent: float = Field(..., ge=0.0, le=100.0)
    band_score: float = Field(
        ...,
        ge=0.0,
        le=9.0,
        description="Official IELTS 0.0-9.0 Band score.",
    )
    cefr_standard_score: float = Field(
        ...,
        ge=0.0,
        le=75.0,
        description="Uzbekistan Multi-level 0-75 standard score.",
    )
    cefr_level: CEFRLevel = Field(
        ...,
        description="Mapped CEFR level ('BELOW_B1', 'B1', 'B2', 'C1').",
    )
    api_cost_usd: float = Field(
        default=0.0,
        description="Always $0.00 — graded deterministically without LLM tokens.",
    )
    question_results: list[ObjectiveQuestionResult] = Field(default_factory=list)


class ReadingListeningScorer:
    """Zero-token ($0.00 API cost) deterministic grader for Listening and Reading."""

    @staticmethod
    def score_section(
        user_answers: Mapping[str | int, Any] | Sequence[Any],
        answer_key: Mapping[str | int, str | Sequence[str]] | Sequence[str | Sequence[str]],
        section: SkillSection = "listening",
        exam_type: ExamType = "IELTS",
        reading_module: ReadingModule = "academic",
    ) -> ObjectiveSectionScoreResult:
        """Grade a Listening or Reading submission deterministically against an answer key."""
        if isinstance(answer_key, Mapping):
            key_items = [(str(k), v) for k, v in answer_key.items()]
        else:
            key_items = [(str(idx + 1), v) for idx, v in enumerate(answer_key)]

        if not key_items:
            raise ValueError("answer_key cannot be empty.")

        if isinstance(user_answers, Mapping):
            user_map = {str(k): v for k, v in user_answers.items()}
        else:
            user_map = {str(idx + 1): v for idx, v in enumerate(user_answers)}

        question_results: list[ObjectiveQuestionResult] = []
        correct_count = 0

        for q_id, expected in key_items:
            raw_user = user_map.get(q_id, "")
            matched = is_objective_answer_correct(raw_user, expected)
            if matched:
                correct_count += 1

            display_expected = (
                expected
                if isinstance(expected, str)
                else " / ".join(str(x) for x in expected)
            )
            question_results.append(
                ObjectiveQuestionResult(
                    question_id=q_id,
                    user_answer="" if raw_user is None else str(raw_user).strip(),
                    correct_answer=display_expected,
                    is_correct=matched,
                )
            )

        total_questions = len(key_items)
        accuracy_percent = round((correct_count / float(total_questions)) * 100.0, 2)

        # Scale raw count to 40-question equivalent if a custom question count is used
        scaled_40 = round((correct_count / float(total_questions)) * 40)

        if section == "listening":
            band_score = convert_listening_raw_to_band(scaled_40)
        else:
            band_score = convert_reading_raw_to_band(scaled_40, module=reading_module)

        cefr_standard_score = convert_raw_to_cefr_standard_score(
            correct_count=correct_count,
            total_questions=total_questions,
        )

        if exam_type == "CEFR":
            cefr_level = map_cefr_score_to_level(cefr_standard_score)
        else:
            cefr_level = map_ielts_band_to_cefr_level(band_score)

        return ObjectiveSectionScoreResult(
            section=section,
            exam_type=exam_type,
            reading_module=reading_module,
            correct_count=correct_count,
            total_questions=total_questions,
            accuracy_percent=accuracy_percent,
            band_score=band_score,
            cefr_standard_score=cefr_standard_score,
            cefr_level=cefr_level,
            api_cost_usd=0.0,
            question_results=question_results,
        )


def score_reading_or_listening(
    user_answers: Mapping[str | int, Any] | Sequence[Any],
    answer_key: Mapping[str | int, str | Sequence[str]] | Sequence[str | Sequence[str]],
    section: SkillSection = "listening",
    exam_type: ExamType = "IELTS",
    reading_module: ReadingModule = "academic",
) -> ObjectiveSectionScoreResult:
    """Module-level helper for deterministic Listening/Reading evaluation."""
    return ReadingListeningScorer.score_section(
        user_answers=user_answers,
        answer_key=answer_key,
        section=section,
        exam_type=exam_type,
        reading_module=reading_module,
    )
