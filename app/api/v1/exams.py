"""FastAPI v1 endpoints for the IELTS & CEFR mock platform (`/api/v1/...`).

Free tier: Listening/Reading scoring is unlimited (no AI cost). AI-scored submissions
(full mock, Writing, Speaking) are limited to `DAILY_EXAM_LIMIT` per person per day.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.identity import Caller, resolve_caller
from app.bot.handlers.exam_flow import (
    AIServiceUnavailableError,
    evaluate_speaking_with_demo_fallback,
    evaluate_writing_with_demo_fallback,
    is_placeholder_api_key,
    transcribe_voice_with_demo_fallback,
)
from app.core.config import BASE_DIR, settings
from app.schemas.report import FullExamReportData
from app.schemas.speaking import SpeakingEvaluationRequest, SpeakingEvaluationResult
from app.schemas.writing import ExamType, WritingEvaluationRequest, WritingEvaluationResult
from app.services import usage_limits
from app.services.chart_renderer import render_task1_chart
from app.services.demo_exam_bank import get_demo_test_by_id, get_demo_tests, sanitize_test_for_client
from app.services.exam_orchestrator import get_exam_orchestrator_service
from app.services.pdf_generator import PDFReportGeneratorService
from app.services.reading_listening_scorer import score_reading_or_listening
from app.services.report_tokens import decode_report_token, encode_report_token

logger = logging.getLogger(__name__)
router = APIRouter()

# ~6 MB decoded; the Mini App downsizes photos before upload.
MAX_IMAGE_BASE64_CHARS = 8_000_000
# ~2.5 min of 16 kHz mono WAV.
MAX_AUDIO_BASE64_CHARS = 7_000_000

FeedbackLanguage = Literal["uz", "ru", "en"]

AI_UNAVAILABLE_DETAIL = (
    "The AI examiner is temporarily unavailable. Your answers were not scored and this attempt "
    "was not counted — please try again shortly."
)


# =====================================================================
# Schemas
# =====================================================================


class ObjectiveSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_id: str | None = None
    exam_type: ExamType = "IELTS"
    listening_answers: dict[str, Any] | None = None
    reading_answers: dict[str, Any] | None = None


class WritingSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_id: str | None = None
    exam_type: ExamType = "IELTS"
    feedback_language: FeedbackLanguage = "uz"
    task_1_text: str | None = Field(default=None, max_length=20_000)
    task_2_text: str | None = Field(default=None, max_length=20_000)
    task_1_image_base64: str | None = Field(default=None, max_length=MAX_IMAGE_BASE64_CHARS)
    task_2_image_base64: str | None = Field(default=None, max_length=MAX_IMAGE_BASE64_CHARS)


class SpeakingSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_id: str | None = None
    exam_type: ExamType = "IELTS"
    feedback_language: FeedbackLanguage = "uz"
    part_1_text: str | None = Field(default=None, max_length=20_000)
    part_2_text: str | None = Field(default=None, max_length=20_000)
    part_3_text: str | None = Field(default=None, max_length=20_000)
    part_1_duration: float | None = Field(default=None, ge=0, le=3600)
    part_2_duration: float | None = Field(default=None, ge=0, le=3600)
    part_3_duration: float | None = Field(default=None, ge=0, le=3600)


class FullReportSubmissionRequest(WritingSubmission, SpeakingSubmission):
    candidate_name: str = Field(default="Candidate", min_length=1, max_length=80)
    listening_answers: dict[str, Any] | None = None
    reading_answers: dict[str, Any] | None = None


class TranscribeRequest(BaseModel):
    audio_base64: str = Field(..., min_length=100, max_length=MAX_AUDIO_BASE64_CHARS)
    filename: str = Field(default="answer.wav", max_length=40)
    duration_seconds: float = Field(default=15.0, ge=0, le=600)
    part_number: Literal[1, 2, 3] = 1


# =====================================================================
# Helpers
# =====================================================================


def _resolve_test(test_id: str | None, exam_type: str) -> dict[str, Any]:
    test = get_demo_test_by_id(test_id or ("CEFR-MOCK-01" if exam_type == "CEFR" else "IELTS-MOCK-01"))
    if test is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Mock test '{test_id}' not found.")
    return test


def _task1_prompt_with_chart(test: dict[str, Any]) -> str:
    writing = test["writing_data"]
    prompt = writing["task_1_prompt"]
    if writing.get("task_1_chart_text"):
        prompt += "\n\nDATA SHOWN IN THE VISUAL (use it to check the accuracy of reported figures):\n"
        prompt += writing["task_1_chart_text"]
    return prompt


async def _consume_exam_quota(caller: Caller) -> None:
    decision = await usage_limits.consume(usage_limits.EXAM, caller.subjects)
    if not decision.allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Daily limit reached: {decision.limit} AI-scored exams per day. Come back tomorrow! "
            "Listening and Reading practice remain unlimited.",
        )


async def _evaluate_writing(test: dict[str, Any], body: WritingSubmission) -> WritingEvaluationResult:
    w_req = WritingEvaluationRequest.model_validate(
        {
            "exam_type": body.exam_type,
            "task_1_prompt": _task1_prompt_with_chart(test),
            "task_1_text": body.task_1_text or "",
            "task_1_image_base64": body.task_1_image_base64 or None,
            "task_2_prompt": test["writing_data"]["task_2_prompt"],
            "task_2_text": body.task_2_text or "",
            "task_2_image_base64": body.task_2_image_base64 or None,
        }
    )
    try:
        return await evaluate_writing_with_demo_fallback(w_req, feedback_language=body.feedback_language)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


async def _evaluate_speaking(test: dict[str, Any], body: SpeakingSubmission) -> SpeakingEvaluationResult:
    sd = test["speaking_data"]
    s_req = SpeakingEvaluationRequest.model_validate(
        {
            "exam_type": body.exam_type,
            "part_1_prompt": "; ".join(sd["part_1_questions"]),
            "part_1_text": body.part_1_text or "",
            "part_2_prompt": sd["part_2_cue_card"],
            "part_2_text": body.part_2_text or "",
            "part_3_prompt": "; ".join(sd["part_3_questions"]),
            "part_3_text": body.part_3_text or "",
        }
    )
    for part, duration in ((s_req.part_1, body.part_1_duration), (s_req.part_2, body.part_2_duration), (s_req.part_3, body.part_3_duration)):
        if duration:
            part.duration_seconds = duration
    return await evaluate_speaking_with_demo_fallback(s_req, feedback_language=body.feedback_language)


def _reports_dir() -> Path:
    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    if not reports_dir.is_absolute():
        reports_dir = BASE_DIR / reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


async def _send_pdf_to_telegram(chat_id: int, pdf_path: Path, scores: dict[str, Any], exam_type: str) -> None:
    """Best effort: deliver the PDF to the candidate's chat with the bot (reliable inside Telegram)."""
    if is_placeholder_api_key(settings.BOT_TOKEN) or ":" not in settings.BOT_TOKEN:
        return
    from aiogram.types import FSInputFile

    from app.bot import create_bot

    bot = create_bot()
    try:
        headline = (
            f"Overall band: <b>{scores.get('overall_band')}</b>" if exam_type == "IELTS"
            else f"Overall: <b>{scores.get('overall_score_75')}/75</b> ({scores.get('cefr_level')})"
        )
        await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(pdf_path),
            caption=f"📄 Your {exam_type} mock report is ready.\n{headline}",
        )
    except Exception as exc:
        logger.info("Could not send PDF to Telegram chat %s: %s", chat_id, exc)
    finally:
        await bot.session.close()


# =====================================================================
# System, config & exam bank
# =====================================================================


@router.get("/health", tags=["System"])
async def api_v1_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.APP_ENV, "version": "0.3.1"}


@router.get("/config", tags=["System"])
async def public_config() -> dict[str, Any]:
    """Public front-end configuration (limits, ad slots, bot link)."""
    return {
        "daily_exam_limit": settings.DAILY_EXAM_LIMIT,
        "bot_username": settings.BOT_USERNAME,
        "ads": {
            "adsgram_block_id": settings.ADSGRAM_BLOCK_ID or None,
            "adsense_client_id": settings.ADSENSE_CLIENT_ID or None,
            "adsense_slot_id": settings.ADSENSE_SLOT_ID or None,
        },
    }


@router.get("/quota", tags=["System"])
async def my_quota(request: Request) -> dict[str, int]:
    decision = await usage_limits.remaining(usage_limits.EXAM, resolve_caller(request).subjects)
    return {"limit": decision.limit, "used": decision.used, "remaining": decision.remaining}


@router.get("/tests", tags=["Mock Exams"])
async def list_mock_tests(exam_type: str | None = Query(default=None)) -> list[dict[str, Any]]:
    return [sanitize_test_for_client(t) for t in get_demo_tests(exam_type=exam_type)]


@router.get("/tests/{test_id}", tags=["Mock Exams"])
async def get_mock_test(test_id: str) -> dict[str, Any]:
    test = get_demo_test_by_id(test_id)
    if test is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Mock test '{test_id}' not found.")
    return sanitize_test_for_client(test)


@router.get("/tests/{test_id}/task1-chart.png", tags=["Mock Exams"])
async def get_task1_chart(test_id: str) -> Response:
    png = render_task1_chart(test_id.strip().upper())
    if png is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This test has no Task 1 visual.")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


# =====================================================================
# Submissions
# =====================================================================


@router.post("/submissions/objective", tags=["Submissions & Grading"])
async def submit_objective_sections(payload: ObjectiveSubmissionRequest) -> dict[str, Any]:
    """Score Listening and/or Reading deterministically (free, unlimited)."""
    test = _resolve_test(payload.test_id, payload.exam_type)
    exam_type: ExamType = payload.exam_type
    out: dict[str, Any] = {"test_id": test["id"], "exam_type": exam_type, "api_cost_usd": 0.0}
    for section in ("listening", "reading"):
        answers = getattr(payload, f"{section}_answers")
        if answers is None:
            continue
        result = score_reading_or_listening(
            user_answers=answers,
            answer_key=test[f"{section}_data"]["answer_key"],
            section=section,
            exam_type=exam_type,
            reading_module="academic",
        )
        out[section] = result.model_dump(mode="json")
        out[f"{section}_raw"] = result.correct_count
        out[f"{section}_band"] = result.band_score
        out[f"{section}_score_75"] = result.cefr_standard_score
        out[f"{section}_cefr_level"] = result.cefr_level
    return out


@router.post("/submissions/writing", response_model=WritingEvaluationResult, tags=["Submissions & Grading"])
async def submit_writing_evaluation(payload: WritingSubmission, request: Request) -> WritingEvaluationResult:
    test = _resolve_test(payload.test_id, payload.exam_type)
    caller = resolve_caller(request)
    await _consume_exam_quota(caller)
    try:
        return await _evaluate_writing(test, payload)
    except (AIServiceUnavailableError, HTTPException) as exc:
        await usage_limits.refund(usage_limits.EXAM, caller.subjects)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, AI_UNAVAILABLE_DETAIL) from exc


@router.post("/submissions/speaking", response_model=SpeakingEvaluationResult, tags=["Submissions & Grading"])
async def submit_speaking_evaluation(payload: SpeakingSubmission, request: Request) -> SpeakingEvaluationResult:
    test = _resolve_test(payload.test_id, payload.exam_type)
    caller = resolve_caller(request)
    await _consume_exam_quota(caller)
    try:
        return await _evaluate_speaking(test, payload)
    except AIServiceUnavailableError as exc:
        await usage_limits.refund(usage_limits.EXAM, caller.subjects)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, AI_UNAVAILABLE_DETAIL) from exc


@router.post("/speaking/transcribe", tags=["Submissions & Grading"])
async def transcribe_speaking_answer(payload: TranscribeRequest, request: Request) -> dict[str, Any]:
    """Turn one recorded Speaking answer into text (called after each answer during the test)."""
    caller = resolve_caller(request)
    decision = await usage_limits.consume(usage_limits.TRANSCRIBE, caller.subjects)
    if not decision.allowed:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Daily speaking transcription limit reached.")
    try:
        audio = base64.b64decode(payload.audio_base64.split(",", 1)[-1], validate=False)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Audio is not valid base64.") from exc
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "", payload.filename) or "answer.wav"
    try:
        result = await transcribe_voice_with_demo_fallback(
            audio_bytes=audio,
            duration_seconds=payload.duration_seconds,
            part_number=payload.part_number,
            filename=safe_name,
        )
    except AIServiceUnavailableError as exc:
        await usage_limits.refund(usage_limits.TRANSCRIBE, caller.subjects)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, AI_UNAVAILABLE_DETAIL) from exc
    return {"transcript": result.transcribed_text, "word_count": result.word_count, "duration_seconds": result.duration_seconds}


@router.post("/submissions/full-report", tags=["Submissions & Grading"])
async def submit_full_exam_report(payload: FullReportSubmissionRequest, request: Request) -> dict[str, Any]:
    """Score all four skills, build the PDF report and return a signed download link."""
    exam_type: ExamType = payload.exam_type
    test = _resolve_test(payload.test_id, exam_type)
    caller = resolve_caller(request)
    await _consume_exam_quota(caller)

    try:
        writing_eval, speaking_eval = await asyncio.gather(
            _evaluate_writing(test, payload),
            _evaluate_speaking(test, payload),
        )
    except (AIServiceUnavailableError, HTTPException) as exc:
        await usage_limits.refund(usage_limits.EXAM, caller.subjects)
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, AI_UNAVAILABLE_DETAIL) from exc

    raw: dict[str, int] = {}
    review: dict[str, Any] = {}
    for section in ("listening", "reading"):
        scored = score_reading_or_listening(
            user_answers=getattr(payload, f"{section}_answers") or {},
            answer_key=test[f"{section}_data"]["answer_key"],
            section=section,
            exam_type=exam_type,
        )
        raw[section] = scored.correct_count
        review[section] = [r.model_dump(mode="json") for r in scored.question_results]

    report_id = f"{exam_type}-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    target_pdf_path = _reports_dir() / f"{report_id}.pdf"
    compiled = await get_exam_orchestrator_service().compile_full_exam_report(
        report_id=report_id,
        candidate_name=payload.candidate_name.strip(),
        candidate_telegram_id=caller.telegram_id,
        exam_type=exam_type,
        verification_url=f"https://t.me/{settings.BOT_USERNAME}",
        listening_raw=raw["listening"],
        reading_raw=raw["reading"],
        writing_evaluation=writing_eval,
        speaking_evaluation=speaking_eval,
        output_path=target_pdf_path,
    )
    report_json = compiled.report_data.model_dump(mode="json")
    token = encode_report_token(report_json)
    scores = compiled.scores.model_dump(mode="json")

    if caller.telegram_id is not None:
        asyncio.create_task(_send_pdf_to_telegram(caller.telegram_id, target_pdf_path, scores, exam_type))

    download_url = f"/api/v1/reports/{report_id}/pdf?t={token}"
    return {
        "report_id": report_id,
        "download_url": download_url,
        "pdf_url": download_url,
        "sent_to_telegram": caller.telegram_id is not None,
        "scores": scores,
        "report_data": report_json,
        "objective_review": review,
    }


@router.get("/reports/{report_id}/pdf", tags=["Reports"])
async def download_exam_report_pdf(report_id: str, t: str | None = Query(default=None, max_length=60_000)) -> Response:
    """Serve a report PDF; if the server restarted and lost it, rebuild it from the signed token."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", report_id.strip())
    if not safe_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid report_id.")
    pdf_path = _reports_dir() / f"{safe_id}.pdf"

    if not pdf_path.is_file():
        if not t:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"PDF report '{safe_id}' not found.")
        try:
            data = decode_report_token(t)
        except ValueError as exc:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
        if data.get("report_id") != safe_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Token does not match this report.")
        PDFReportGeneratorService().generate_and_save(
            report_data=FullExamReportData.model_validate(data), output_path=pdf_path
        )

    return Response(
        content=pdf_path.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_id}.pdf"'},
    )


__all__ = ["router"]
