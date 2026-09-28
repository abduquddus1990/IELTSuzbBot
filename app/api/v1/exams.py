"""FastAPI v1 Endpoints for IELTS & Uzbekistan CEFR Mock AI (`app/api/v1/exams.py`).

Endpoints:
- `GET  /api/v1/health`: Health and readiness check.
- `GET  /api/v1/tests`: List available sanitized demo mock exams (`?exam_type=IELTS|CEFR`).
- `GET  /api/v1/tests/{test_id}`: Fetch a single sanitized mock exam without `answer_key`.
- `POST /api/v1/submissions/objective`: Grade 40 Listening & 40 Reading answers at $0.00 token cost.
- `POST /api/v1/submissions/writing`: Evaluate Writing Task 1 & Task 2 (with anti-jailbreak & demo fallback).
- `POST /api/v1/submissions/speaking`: Evaluate Speaking Parts 1, 2, 3 (with anti-jailbreak & demo fallback).
- `POST /api/v1/submissions/full-report`: Aggregate 4 skills, generate multi-page PDF report, and return download URL.
- `GET  /api/v1/reports/{report_id}/pdf`: Download a generated PDF Certificate & Error Workbook.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.bot.handlers.exam_flow import (
    evaluate_speaking_with_demo_fallback,
    evaluate_writing_with_demo_fallback,
)
from app.core.config import BASE_DIR, settings
from app.schemas.speaking import (
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
)
from app.schemas.writing import (
    ExamType,
    WritingEvaluationRequest,
    WritingEvaluationResult,
)
from app.services.demo_exam_bank import (
    get_demo_test_by_id,
    get_demo_tests,
    sanitize_test_for_client,
)
from app.services.exam_orchestrator import get_exam_orchestrator_service
from app.services.reading_listening_scorer import score_reading_or_listening

router = APIRouter()


# =====================================================================
# 1. REQUEST / RESPONSE SCHEMAS FOR REST ENDPOINTS
# =====================================================================


class ObjectiveSubmissionRequest(BaseModel):
    """Payload for deterministic ($0.00 token cost) Listening & Reading grading."""

    model_config = ConfigDict(extra="ignore")

    test_id: str | None = Field(
        default=None,
        description="ID of the mock test ('IELTS-MOCK-01' or 'CEFR-MOCK-01').",
    )
    exam_type: ExamType = Field(
        default="IELTS",
        description="Target exam format ('IELTS' or 'CEFR').",
    )
    listening_answers: dict[str, Any] | list[Any] = Field(
        default_factory=dict,
        description="Candidate's answers for Listening questions 1..40.",
    )
    reading_answers: dict[str, Any] | list[Any] = Field(
        default_factory=dict,
        description="Candidate's answers for Reading questions 1..40.",
    )


class FullReportSubmissionRequest(BaseModel):
    """Flexible payload for compiling a 4-skill exam report and generating its PDF Certificate."""

    model_config = ConfigDict(extra="ignore")

    report_id: str | None = Field(
        default=None,
        description="Optional custom report ID; auto-generated if omitted.",
    )
    candidate_name: str = Field(
        default="Candidate",
        min_length=1,
        description="Candidate's full name for the PDF certificate.",
    )
    candidate_telegram_id: int | None = Field(
        default=None,
        description="Optional Telegram numeric user ID.",
    )
    test_id: str | None = Field(
        default=None,
        description="Optional test ID ('IELTS-MOCK-01' or 'CEFR-MOCK-01').",
    )
    exam_type: ExamType = Field(
        default="IELTS",
        description="Exam format ('IELTS' or 'CEFR').",
    )

    # Objective Listening & Reading inputs (either raw counts, bands, or answer dicts)
    listening_raw: int | None = Field(default=None, ge=0, le=40)
    listening_band: float | None = Field(default=None, ge=0.0, le=9.0)
    listening_score_75: float | None = Field(default=None, ge=0.0, le=75.0)
    listening_answers: dict[str, Any] | None = Field(default=None)

    reading_raw: int | None = Field(default=None, ge=0, le=40)
    reading_band: float | None = Field(default=None, ge=0.0, le=9.0)
    reading_score_75: float | None = Field(default=None, ge=0.0, le=75.0)
    reading_answers: dict[str, Any] | None = Field(default=None)

    # Writing inputs (pre-computed evaluation, band score, or raw texts)
    writing_band: float | None = Field(default=None, ge=0.0, le=9.0)
    writing_score_75: float | None = Field(default=None, ge=0.0, le=75.0)
    writing_evaluation: WritingEvaluationResult | None = Field(default=None)
    task_1_prompt: str | None = Field(default=None)
    task_1_text: str | None = Field(default=None)
    task_2_prompt: str | None = Field(default=None)
    task_2_text: str | None = Field(default=None)

    # Speaking inputs (pre-computed evaluation, band score, or raw transcripts)
    speaking_band: float | None = Field(default=None, ge=0.0, le=9.0)
    speaking_score_75: float | None = Field(default=None, ge=0.0, le=75.0)
    speaking_evaluation: SpeakingEvaluationResult | None = Field(default=None)
    part_1_prompt: str | None = Field(default=None)
    part_1_text: str | None = Field(default=None)
    part_2_prompt: str | None = Field(default=None)
    part_2_text: str | None = Field(default=None)
    part_3_prompt: str | None = Field(default=None)
    part_3_text: str | None = Field(default=None)


# =====================================================================
# 2. SYSTEM & DEMO EXAM BANK ENDPOINTS
# =====================================================================


@router.get("/health", tags=["System"])
async def api_v1_health() -> dict[str, str]:
    """Liveness and readiness probe for `/api/v1/health`."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }


@router.get("/tests", tags=["Mock Exams"])
async def list_mock_tests(
    exam_type: str | None = Query(
        default=None,
        description="Optional filter by exam type ('IELTS' or 'CEFR').",
    ),
) -> list[dict[str, Any]]:
    """Return available built-in mock exams with `answer_key` stripped for client security."""
    tests = get_demo_tests(exam_type=exam_type)
    return [sanitize_test_for_client(t) for t in tests]


@router.get("/tests/{test_id}", tags=["Mock Exams"])
async def get_mock_test(test_id: str) -> dict[str, Any]:
    """Fetch a single mock exam by ID with `answer_key` stripped from Listening and Reading."""
    test = get_demo_test_by_id(test_id)
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mock test '{test_id}' not found.",
        )
    return sanitize_test_for_client(test)


# =====================================================================
# 3. SUBMISSION & AI EVALUATION ENDPOINTS
# =====================================================================


@router.post("/submissions/objective", tags=["Submissions & Grading"])
async def submit_objective_sections(
    payload: ObjectiveSubmissionRequest,
) -> dict[str, Any]:
    """Grade 40 Listening and 40 Reading answers deterministically at $0.00 token cost."""
    resolved_test_id = payload.test_id or (
        "CEFR-MOCK-01" if payload.exam_type == "CEFR" else "IELTS-MOCK-01"
    )
    test = get_demo_test_by_id(resolved_test_id)
    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mock test '{resolved_test_id}' not found.",
        )

    exam_type: ExamType = payload.exam_type or test.get("exam_type", "IELTS")
    listening_key = test["listening_data"]["answer_key"]
    reading_key = test["reading_data"]["answer_key"]

    listening_result = score_reading_or_listening(
        user_answers=payload.listening_answers,
        answer_key=listening_key,
        section="listening",
        exam_type=exam_type,
    )
    reading_result = score_reading_or_listening(
        user_answers=payload.reading_answers,
        answer_key=reading_key,
        section="reading",
        exam_type=exam_type,
        reading_module="academic",
    )

    return {
        "test_id": test["id"],
        "exam_type": exam_type,
        "api_cost_usd": 0.0,
        "listening": listening_result.model_dump(mode="json"),
        "reading": reading_result.model_dump(mode="json"),
        "listening_raw": listening_result.correct_count,
        "listening_band": listening_result.band_score,
        "listening_score_75": listening_result.cefr_standard_score,
        "listening_cefr_level": listening_result.cefr_level,
        "reading_raw": reading_result.correct_count,
        "reading_band": reading_result.band_score,
        "reading_score_75": reading_result.cefr_standard_score,
        "reading_cefr_level": reading_result.cefr_level,
    }


def _normalize_writing_payload(raw_body: dict[str, Any]) -> WritingEvaluationRequest:
    """Normalize either nested (`task_1`/`task_2`) or flat (`task_1_text`/`task_2_text`) Writing payloads."""
    data = dict(raw_body)
    exam_type = str(data.get("exam_type", "IELTS")).strip().upper()
    default_test = get_demo_test_by_id("CEFR-MOCK-01" if exam_type == "CEFR" else "IELTS-MOCK-01")
    default_t1_prompt = (
        default_test["writing_data"]["task_1_prompt"]
        if default_test
        else "Writing Task 1 Prompt"
    )
    default_t2_prompt = (
        default_test["writing_data"]["task_2_prompt"]
        if default_test
        else "Writing Task 2 Prompt"
    )

    if isinstance(data.get("task_1"), str):
        data["task_1"] = {
            "task_number": 1,
            "prompt_topic": data.pop("task_1_prompt", default_t1_prompt),
            "student_text": data["task_1"],
        }
    if isinstance(data.get("task_2"), str):
        data["task_2"] = {
            "task_number": 2,
            "prompt_topic": data.pop("task_2_prompt", default_t2_prompt),
            "student_text": data["task_2"],
        }

    if "task_1" not in data and "task_1_prompt" not in data:
        data["task_1_prompt"] = default_t1_prompt
    if "task_2" not in data and "task_2_prompt" not in data:
        data["task_2_prompt"] = default_t2_prompt

    return WritingEvaluationRequest.model_validate(data)


@router.post(
    "/submissions/writing",
    response_model=WritingEvaluationResult,
    tags=["Submissions & Grading"],
)
async def submit_writing_evaluation(
    payload: dict[str, Any] = Body(...),
) -> WritingEvaluationResult:
    """Evaluate Writing Task 1 & Task 2 with anti-jailbreak security and graceful demo fallback."""
    request_obj = _normalize_writing_payload(payload)
    return await evaluate_writing_with_demo_fallback(request_obj)


def _normalize_speaking_payload(raw_body: dict[str, Any]) -> SpeakingEvaluationRequest:
    """Normalize either nested (`part_1`..`part_3`) or flat (`part_1_text`..`part_3_text`) Speaking payloads."""
    data = dict(raw_body)
    for part_num in (1, 2, 3):
        key = f"part_{part_num}"
        if isinstance(data.get(key), str):
            data[key] = {
                "part_number": part_num,
                "question_prompt": data.pop(f"{key}_prompt", f"Speaking Part {part_num} Prompt"),
                "transcript_text": data[key],
            }
        elif key not in data and f"{key}_prompt" not in data:
            data[f"{key}_prompt"] = f"Speaking Part {part_num} Prompt"

    return SpeakingEvaluationRequest.model_validate(data)


@router.post(
    "/submissions/speaking",
    response_model=SpeakingEvaluationResult,
    tags=["Submissions & Grading"],
)
async def submit_speaking_evaluation(
    payload: dict[str, Any] = Body(...),
) -> SpeakingEvaluationResult:
    """Evaluate Speaking Parts 1, 2, 3 with anti-jailbreak security and graceful demo fallback."""
    request_obj = _normalize_speaking_payload(payload)
    return await evaluate_speaking_with_demo_fallback(request_obj)


@router.post("/submissions/full-report", tags=["Submissions & Grading"])
async def submit_full_exam_report(
    payload: FullReportSubmissionRequest,
) -> dict[str, Any]:
    """Compile all 4 skills, generate the 2-3 page PDF report in `storage/reports/`, and return metadata."""
    exam_type: ExamType = payload.exam_type
    resolved_test_id = payload.test_id or (
        "CEFR-MOCK-01" if exam_type == "CEFR" else "IELTS-MOCK-01"
    )
    test = get_demo_test_by_id(resolved_test_id) or get_demo_test_by_id("IELTS-MOCK-01")
    assert test is not None

    # 1. Resolve Listening raw score if answers dictionary was provided
    l_raw = payload.listening_raw
    if l_raw is None and payload.listening_answers is not None:
        l_scored = score_reading_or_listening(
            user_answers=payload.listening_answers,
            answer_key=test["listening_data"]["answer_key"],
            section="listening",
            exam_type=exam_type,
        )
        l_raw = l_scored.correct_count

    # 2. Resolve Reading raw score if answers dictionary was provided
    r_raw = payload.reading_raw
    if r_raw is None and payload.reading_answers is not None:
        r_scored = score_reading_or_listening(
            user_answers=payload.reading_answers,
            answer_key=test["reading_data"]["answer_key"],
            section="reading",
            exam_type=exam_type,
        )
        r_raw = r_scored.correct_count

    # 3. Resolve Writing evaluation if raw task_1_text / task_2_text were provided
    writing_eval = payload.writing_evaluation
    if writing_eval is None and (payload.task_1_text or payload.task_2_text):
        w_req = WritingEvaluationRequest.model_validate(
            {
                "exam_type": exam_type,
                "task_1_prompt": payload.task_1_prompt or test["writing_data"]["task_1_prompt"],
                "task_1_text": payload.task_1_text or "",
                "task_2_prompt": payload.task_2_prompt or test["writing_data"]["task_2_prompt"],
                "task_2_text": payload.task_2_text or "",
            }
        )
        writing_eval = await evaluate_writing_with_demo_fallback(w_req)

    # 4. Resolve Speaking evaluation if raw part_1_text..part_3_text were provided
    speaking_eval = payload.speaking_evaluation
    if speaking_eval is None and (
        payload.part_1_text or payload.part_2_text or payload.part_3_text
    ):
        s_req = SpeakingEvaluationRequest.model_validate(
            {
                "exam_type": exam_type,
                "part_1_prompt": payload.part_1_prompt or "Speaking Part 1 Interview",
                "part_1_text": payload.part_1_text or "",
                "part_2_prompt": payload.part_2_prompt or test["speaking_data"]["part_2_cue_card"],
                "part_2_text": payload.part_2_text or "",
                "part_3_prompt": payload.part_3_prompt or "Speaking Part 3 Discussion",
                "part_3_text": payload.part_3_text or "",
            }
        )
        speaking_eval = await evaluate_speaking_with_demo_fallback(s_req)

    # 5. Generate unique report_id and compile PDF report
    if payload.report_id and payload.report_id.strip():
        report_id = re.sub(r"[^A-Za-z0-9_-]", "-", payload.report_id.strip())
    else:
        short_uuid = uuid.uuid4().hex[:6].upper()
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        report_id = f"{exam_type}-{date_str}-{short_uuid}"

    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    if not reports_dir.is_absolute():
        reports_dir = BASE_DIR / reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    target_pdf_path = reports_dir / f"{report_id}.pdf"

    orchestrator = get_exam_orchestrator_service()
    compiled = await orchestrator.compile_full_exam_report(
        report_id=report_id,
        candidate_name=payload.candidate_name,
        candidate_telegram_id=payload.candidate_telegram_id,
        exam_type=exam_type,
        listening_raw=l_raw,
        listening_band=payload.listening_band,
        listening_score_75=payload.listening_score_75,
        reading_raw=r_raw,
        reading_band=payload.reading_band,
        reading_score_75=payload.reading_score_75,
        writing_band=payload.writing_band,
        writing_score_75=payload.writing_score_75,
        writing_evaluation=writing_eval,
        speaking_band=payload.speaking_band,
        speaking_score_75=payload.speaking_score_75,
        speaking_evaluation=speaking_eval,
        output_path=target_pdf_path,
    )

    download_url = f"/api/v1/reports/{report_id}/pdf"
    return {
        "report_id": report_id,
        "download_url": download_url,
        "pdf_url": download_url,
        "scores": compiled.scores.model_dump(mode="json"),
        "report_data": compiled.report_data.model_dump(mode="json"),
    }


@router.get("/reports/{report_id}/pdf", tags=["Reports"])
async def download_exam_report_pdf(report_id: str) -> Response:
    """Download a generated multi-page PDF Certificate & Error Workbook by `report_id`."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", report_id.strip())
    if not safe_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_id.",
        )

    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    if not reports_dir.is_absolute():
        reports_dir = BASE_DIR / reports_dir

    pdf_path = reports_dir / f"{safe_id}.pdf"
    if not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report '{safe_id}' not found.",
        )

    pdf_bytes = pdf_path.read_bytes()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_id}.pdf"',
        },
    )


__all__ = ["router"]
