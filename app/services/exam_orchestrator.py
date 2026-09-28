"""Full 4-Skill Exam Orchestrator Service for IELTS & Uzbekistan National CEFR (Multi-Level).

Coordinates:
1. `build_section_score_summary`:
   - Converts raw Listening/Reading counts (0-40) or Band scores (0.0-9.0) into both
     official IELTS Bands (with `.25` / `.75` overall rounding via `round_ielts_overall_band`)
     and Uzbekistan BBA Multi-Level standard scores (`0 - 75` scale via `band_to_cefr_75_score`).
   - Integrates `WritingEvaluationResult` and `SpeakingEvaluationResult` scores.
2. `compile_full_exam_report`:
   - Combines 4-skill scores, Writing evaluation, and Speaking evaluation into `FullExamReportData`.
   - Generates the multi-page diagnostic PDF Certificate & Error Workbook via `PDFReportGeneratorService`.
   - Optionally uploads the generated PDF to Cloudflare R2 (or local storage fallback) via `R2StorageService`.
"""

from __future__ import annotations

import inspect
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Literal

from app.core.config import BASE_DIR, settings
from app.schemas.report import (
    FullExamReportData,
    SectionScoreSummary,
    band_to_cefr_75_score,
)
from app.schemas.speaking import SpeakingEvaluationResult
from app.schemas.writing import CEFRLevel, ExamType, WritingEvaluationResult
from app.services.pdf_generator import PDFReportGeneratorService
from app.services.reading_listening_scorer import (
    ReadingModule,
    convert_listening_raw_to_band,
    convert_raw_to_cefr_standard_score,
    convert_reading_raw_to_band,
    map_cefr_score_to_level,
    map_ielts_band_to_cefr_level,
    round_ielts_overall_band,
    round_to_half_band,
)

logger = logging.getLogger(__name__)


# =====================================================================
# 1. CLOUDFLARE R2 STORAGE FALLBACK ADAPTER (IF r2_storage.py ABSENT)
# =====================================================================


class _FallbackR2StorageService:
    """Zero-egress Cloudflare R2 (S3-compatible) storage service with automatic local fallback."""

    def __init__(
        self,
        bucket_name: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_domain: str | None = None,
        local_fallback_dir: str | Path | None = None,
        s3_client: Any = None,
    ) -> None:
        self.bucket_name = bucket_name or settings.R2_BUCKET_NAME
        self.endpoint_url = endpoint_url or settings.R2_ENDPOINT_URL
        self.access_key_id = access_key_id or settings.R2_ACCESS_KEY_ID
        self.secret_access_key = secret_access_key or settings.R2_SECRET_ACCESS_KEY
        self.public_domain = (public_domain or settings.R2_PUBLIC_DOMAIN).rstrip("/")
        self._s3_client = s3_client

        raw_local = local_fallback_dir or (BASE_DIR / "storage" / "r2_local")
        local_path = Path(raw_local)
        if not local_path.is_absolute():
            local_path = BASE_DIR / local_path
        self.local_fallback_dir = local_path
        self.local_fallback_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        """Return True if real Cloudflare R2 credentials are configured (not placeholders)."""
        placeholders = {
            "",
            "your_cloudflare_account_id",
            "your_r2_access_key_id",
            "your_r2_secret_access_key",
        }
        if self._s3_client is not None:
            return True
        return (
            self.access_key_id not in placeholders
            and self.secret_access_key not in placeholders
            and "your_cloudflare_account_id" not in self.endpoint_url
        )

    def _save_locally(self, object_key: str, data: bytes) -> Path:
        """Persist bytes to `storage/r2_local/<object_key>` when R2 is not configured."""
        clean_key = object_key.lstrip("/\\").replace("..", "_")
        target = self.local_fallback_dir / clean_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    async def upload_bytes(
        self,
        data: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to R2 or local fallback and return the public URL or local path."""
        clean_key = object_key.lstrip("/")
        if self.is_configured and self._s3_client is not None:
            put_fn = getattr(self._s3_client, "put_object", None)
            if callable(put_fn):
                res = put_fn(
                    Bucket=self.bucket_name,
                    Key=clean_key,
                    Body=data,
                    ContentType=content_type,
                )
                if inspect.isawaitable(res):
                    await res
                return f"{self.public_domain}/{clean_key}"

        local_path = self._save_locally(clean_key, data)
        return str(local_path)

    async def upload_pdf(
        self,
        pdf_bytes: bytes,
        report_id: str,
        object_key: str | None = None,
    ) -> str:
        """Upload a generated PDF report to R2 or local fallback."""
        key = object_key or f"reports/{report_id}.pdf"
        return await self.upload_bytes(
            data=pdf_bytes,
            object_key=key,
            content_type="application/pdf",
        )

    async def upload_audio(
        self,
        audio_bytes: bytes,
        filename: str = "voice.ogg",
        object_key: str | None = None,
        content_type: str = "audio/ogg",
    ) -> str:
        """Upload a Speaking voice recording to R2 or local fallback."""
        key = object_key or f"audio/{filename}"
        return await self.upload_bytes(
            data=audio_bytes,
            object_key=key,
            content_type=content_type,
        )


def _resolve_r2_storage_class() -> type:
    """Import `R2StorageService` from `app.services.r2_storage` if present, else use fallback."""
    try:
        from app.services.r2_storage import R2StorageService as _RealR2  # type: ignore[import-not-found]

        return _RealR2
    except ImportError:
        return _FallbackR2StorageService


R2StorageService = _resolve_r2_storage_class()


# =====================================================================
# 2. COMPILED EXAM REPORT RESULT (SYNC + ASYNC + UNPACKING COMPATIBLE)
# =====================================================================


class CompiledExamReportResult:
    """Result container returned by `ExamOrchestratorService.compile_full_exam_report`.

    Supports:
    - Direct attribute access (`result.report_data`, `result.pdf_bytes`, `result.pdf_path`,
      `result.storage_url`, `result.scores`, `result.report_id`, etc.)
    - Tuple unpacking (`report_data, pdf_bytes = orchestrator.compile_full_exam_report(...)`)
    - Async awaiting (`result = await orchestrator.compile_full_exam_report(...)`)
    """

    def __init__(
        self,
        report_data: FullExamReportData,
        pdf_bytes: bytes,
        pdf_path: Path,
        storage_url: str | None = None,
        pending_async_upload: Callable[[], Any] | None = None,
    ) -> None:
        self.report_data = report_data
        self.pdf_bytes = pdf_bytes
        self.pdf_path = pdf_path
        self.storage_url = storage_url
        self._pending_async_upload = pending_async_upload

    @property
    def scores(self) -> SectionScoreSummary:
        """Shortcut to `report_data.scores`."""
        return self.report_data.scores

    def __getattr__(self, name: str) -> Any:
        """Delegate `FullExamReportData` attributes (`report_id`, `candidate_name`, etc.)."""
        return getattr(self.report_data, name)

    def __iter__(self) -> Iterator[Any]:
        """Support 2-tuple unpacking: `report_data, pdf_bytes = compile_full_exam_report(...)`."""
        yield self.report_data
        yield self.pdf_bytes

    def __await__(self) -> Any:
        """Allow `await orchestrator.compile_full_exam_report(...)` in async contexts."""

        async def _resolve() -> CompiledExamReportResult:
            if self._pending_async_upload is not None:
                res = self._pending_async_upload()
                if inspect.isawaitable(res):
                    res = await res
                if isinstance(res, str):
                    self.storage_url = res
                elif hasattr(res, "url") or hasattr(res, "public_url") or hasattr(res, "local_path"):
                    self.storage_url = str(
                        getattr(res, "public_url", None)
                        or getattr(res, "url", None)
                        or getattr(res, "local_path", "")
                    )
                self._pending_async_upload = None
            return self

        return _resolve().__await__()


# =====================================================================
# 3. EXAM ORCHESTRATOR SERVICE
# =====================================================================


class ExamOrchestratorService:
    """Coordinates 4-skill IELTS & CEFR score aggregation, overall rounding, and PDF generation."""

    def __init__(
        self,
        pdf_generator: PDFReportGeneratorService | None = None,
        r2_storage: Any | None = None,
    ) -> None:
        self.pdf_generator = pdf_generator or PDFReportGeneratorService()
        self.r2_storage = r2_storage

    @staticmethod
    def build_section_score_summary(
        *,
        listening_raw: int | None = None,
        listening_band: float | None = None,
        listening_score_75: float | None = None,
        reading_raw: int | None = None,
        reading_band: float | None = None,
        reading_score_75: float | None = None,
        reading_module: ReadingModule = "academic",
        writing_band: float | None = None,
        writing_score_75: float | None = None,
        writing_evaluation: WritingEvaluationResult | None = None,
        speaking_band: float | None = None,
        speaking_score_75: float | None = None,
        speaking_evaluation: SpeakingEvaluationResult | None = None,
        exam_type: ExamType = "IELTS",
    ) -> SectionScoreSummary:
        """Compute dual-scale (`0.0-9.0` Band and `0-75` BBA) scores across all 4 skills."""
        # 1. Listening
        l_raw = max(0, min(40, int(listening_raw))) if listening_raw is not None else 0
        if listening_band is not None:
            l_band = round_to_half_band(listening_band)
        elif listening_raw is not None:
            l_band = convert_listening_raw_to_band(l_raw)
        else:
            l_band = 0.0

        if listening_score_75 is not None:
            l_75 = round(min(75.0, max(0.0, float(listening_score_75))), 1)
        elif listening_raw is not None and listening_band is None and exam_type == "CEFR":
            l_75 = convert_raw_to_cefr_standard_score(l_raw, total_questions=40)
        else:
            l_75 = band_to_cefr_75_score(l_band)

        # 2. Reading
        r_raw = max(0, min(40, int(reading_raw))) if reading_raw is not None else 0
        if reading_band is not None:
            r_band = round_to_half_band(reading_band)
        elif reading_raw is not None:
            r_band = convert_reading_raw_to_band(r_raw, module=reading_module)
        else:
            r_band = 0.0

        if reading_score_75 is not None:
            r_75 = round(min(75.0, max(0.0, float(reading_score_75))), 1)
        elif reading_raw is not None and reading_band is None and exam_type == "CEFR":
            r_75 = convert_raw_to_cefr_standard_score(r_raw, total_questions=40)
        else:
            r_75 = band_to_cefr_75_score(r_band)

        # 3. Writing
        if writing_band is not None:
            w_band = round_to_half_band(writing_band)
        elif writing_evaluation is not None:
            raw_w = writing_evaluation.overall_writing_score
            w_band = (
                round_to_half_band(raw_w)
                if raw_w <= 9.0
                else round_to_half_band((raw_w / 75.0) * 9.0)
            )
        else:
            w_band = 0.0

        if writing_score_75 is not None:
            w_75 = round(min(75.0, max(0.0, float(writing_score_75))), 1)
        elif writing_evaluation is not None and writing_evaluation.overall_writing_score > 9.0:
            w_75 = round(min(75.0, writing_evaluation.overall_writing_score), 1)
        else:
            w_75 = band_to_cefr_75_score(w_band)

        # 4. Speaking
        if speaking_band is not None:
            s_band = round_to_half_band(speaking_band)
        elif speaking_evaluation is not None:
            raw_s = speaking_evaluation.overall_speaking_score
            s_band = (
                round_to_half_band(raw_s)
                if raw_s <= 9.0
                else round_to_half_band((raw_s / 75.0) * 9.0)
            )
        else:
            s_band = 0.0

        if speaking_score_75 is not None:
            s_75 = round(min(75.0, max(0.0, float(speaking_score_75))), 1)
        elif speaking_evaluation is not None and speaking_evaluation.standard_score_75 > 0.0:
            s_75 = round(min(75.0, speaking_evaluation.standard_score_75), 1)
        else:
            s_75 = band_to_cefr_75_score(s_band)

        # 5. Overall IELTS Band (.25 / .75 official rule) & Overall BBA 0-75 Score
        overall_band = round_ielts_overall_band(l_band, r_band, w_band, s_band)
        overall_score_75 = round((l_75 + r_75 + w_75 + s_75) / 4.0, 1)

        if exam_type == "CEFR":
            cefr_level: CEFRLevel = map_cefr_score_to_level(overall_score_75)
        else:
            cefr_level = map_ielts_band_to_cefr_level(overall_band)

        return SectionScoreSummary(
            listening_raw=l_raw,
            listening_band=l_band,
            listening_score_75=l_75,
            reading_raw=r_raw,
            reading_band=r_band,
            reading_score_75=r_75,
            writing_band=w_band,
            writing_score_75=w_75,
            speaking_band=s_band,
            speaking_score_75=s_75,
            overall_band=overall_band,
            overall_score_75=overall_score_75,
            cefr_level=cefr_level,
        )

    def compile_full_exam_report(
        self,
        *,
        report_id: str = "MOCK-2026-0001",
        candidate_name: str = "Candidate",
        candidate_telegram_id: int | None = None,
        exam_type: Literal["IELTS", "CEFR"] = "IELTS",
        exam_date: str | None = None,
        verification_url: str = "https://t.me/ielts_cefr_mock_ai_bot",
        listening_raw: int | None = None,
        listening_band: float | None = None,
        listening_score_75: float | None = None,
        reading_raw: int | None = None,
        reading_band: float | None = None,
        reading_score_75: float | None = None,
        reading_module: ReadingModule = "academic",
        writing_band: float | None = None,
        writing_score_75: float | None = None,
        writing_evaluation: WritingEvaluationResult | None = None,
        speaking_band: float | None = None,
        speaking_score_75: float | None = None,
        speaking_evaluation: SpeakingEvaluationResult | None = None,
        scores: SectionScoreSummary | None = None,
        disclaimer_text: str | None = None,
        output_path: str | Path | None = None,
        upload_to_r2: bool = False,
    ) -> CompiledExamReportResult:
        """Aggregate 4-skill scores, generate the multi-page PDF report, and optionally store in R2."""
        resolved_scores = scores or self.build_section_score_summary(
            listening_raw=listening_raw,
            listening_band=listening_band,
            listening_score_75=listening_score_75,
            reading_raw=reading_raw,
            reading_band=reading_band,
            reading_score_75=reading_score_75,
            reading_module=reading_module,
            writing_band=writing_band,
            writing_score_75=writing_score_75,
            writing_evaluation=writing_evaluation,
            speaking_band=speaking_band,
            speaking_score_75=speaking_score_75,
            speaking_evaluation=speaking_evaluation,
            exam_type=exam_type,
        )

        report_data = FullExamReportData(
            report_id=report_id,
            candidate_name=candidate_name,
            candidate_telegram_id=candidate_telegram_id,
            exam_type=exam_type,
            exam_date=exam_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            verification_url=verification_url,
            scores=resolved_scores,
            writing_evaluation=writing_evaluation,
            speaking_evaluation=speaking_evaluation,
            disclaimer_text=disclaimer_text or settings.PDF_DISCLAIMER_TEXT,
        )

        pdf_bytes, saved_path = self.pdf_generator.generate_and_save(
            report_data=report_data,
            output_path=output_path,
        )

        storage_url: str | None = str(saved_path)
        pending_async: Callable[[], Any] | None = None

        if upload_to_r2 or self.r2_storage is not None:
            storage_svc = self.r2_storage
            if storage_svc is None:
                r2_cls = _resolve_r2_storage_class()
                storage_svc = r2_cls()

            upload_fn = (
                getattr(storage_svc, "upload_pdf", None)
                or getattr(storage_svc, "upload_pdf_report", None)
                or getattr(storage_svc, "upload_bytes", None)
            )
            if callable(upload_fn):
                def _invoke_upload() -> Any:
                    sig = inspect.signature(upload_fn)
                    params = list(sig.parameters.keys())
                    if "pdf_bytes" in params and "report_id" in params:
                        return upload_fn(pdf_bytes=pdf_bytes, report_id=report_id)
                    if "data" in params and "object_key" in params:
                        return upload_fn(
                            data=pdf_bytes,
                            object_key=f"reports/{report_id}.pdf",
                            content_type="application/pdf",
                        )
                    return upload_fn(pdf_bytes, f"reports/{report_id}.pdf")

                if inspect.iscoroutinefunction(upload_fn):
                    pending_async = _invoke_upload
                else:
                    res = _invoke_upload()
                    if inspect.isawaitable(res):
                        pending_async = lambda: res  # noqa: E731
                    elif isinstance(res, str):
                        storage_url = res

        return CompiledExamReportResult(
            report_data=report_data,
            pdf_bytes=pdf_bytes,
            pdf_path=saved_path,
            storage_url=storage_url,
            pending_async_upload=pending_async,
        )


_default_orchestrator: ExamOrchestratorService | None = None


def get_exam_orchestrator_service() -> ExamOrchestratorService:
    """Return a singleton instance of `ExamOrchestratorService`."""
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = ExamOrchestratorService()
    return _default_orchestrator


def build_section_score_summary(**kwargs: Any) -> SectionScoreSummary:
    """Module-level convenience wrapper for `ExamOrchestratorService.build_section_score_summary`."""
    return ExamOrchestratorService.build_section_score_summary(**kwargs)


def compile_full_exam_report(**kwargs: Any) -> CompiledExamReportResult:
    """Module-level convenience wrapper for `ExamOrchestratorService.compile_full_exam_report`."""
    return get_exam_orchestrator_service().compile_full_exam_report(**kwargs)


__all__ = [
    "CompiledExamReportResult",
    "ExamOrchestratorService",
    "R2StorageService",
    " band_to_cefr_75_score".strip(),
    "build_section_score_summary",
    "compile_full_exam_report",
    "get_exam_orchestrator_service",
]
