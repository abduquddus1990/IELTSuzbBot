"""Repository for creating and querying ExamScore evaluation results and PDF reports."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CEFRLevel, ExamType
from app.models.score import ExamScore
from app.repositories.base import BaseRepository


class ScoreRepository(BaseRepository[ExamScore]):
    """Asynchronous data access layer for `ExamScore` records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=ExamScore)

    async def get_by_submission_id(self, submission_id: int) -> ExamScore | None:
        """Retrieve the ExamScore associated with a specific `TestSubmission` ID."""
        stmt = select(ExamScore).where(ExamScore.submission_id == submission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_score(
        self,
        *,
        submission_id: int,
        user_id: int,
        exam_type: ExamType,
        listening_raw: int = 0,
        listening_score: float = 0.0,
        reading_raw: int = 0,
        reading_score: float = 0.0,
        writing_task_1_score: float = 0.0,
        writing_task_2_score: float = 0.0,
        writing_overall_score: float = 0.0,
        speaking_score: float = 0.0,
        overall_score: float = 0.0,
        cefr_level: CEFRLevel = CEFRLevel.BELOW_B1,
        writing_criteria: dict[str, Any] | None = None,
        writing_detailed_errors: list[dict[str, Any]] | None = None,
        writing_band_booster: list[dict[str, Any]] | None = None,
        speaking_feedback: dict[str, Any] | None = None,
        ai_tokens_used: int = 0,
        ai_cost_usd: float = 0.0,
        pdf_report_r2_key: str | None = None,
        pdf_local_path: str | None = None,
    ) -> ExamScore:
        """Create or update the `ExamScore` record for a given `submission_id`."""
        existing = await self.get_by_submission_id(submission_id)
        payload: dict[str, Any] = {
            "user_id": user_id,
            "exam_type": exam_type,
            "listening_raw": listening_raw,
            "listening_score": listening_score,
            "reading_raw": reading_raw,
            "reading_score": reading_score,
            "writing_task_1_score": writing_task_1_score,
            "writing_task_2_score": writing_task_2_score,
            "writing_overall_score": writing_overall_score,
            "speaking_score": speaking_score,
            "overall_score": overall_score,
            "cefr_level": cefr_level,
            "writing_criteria": writing_criteria or {},
            "writing_detailed_errors": writing_detailed_errors or [],
            "writing_band_booster": writing_band_booster or [],
            "speaking_feedback": speaking_feedback or {},
            "ai_tokens_used": ai_tokens_used,
            "ai_cost_usd": ai_cost_usd,
            "pdf_report_r2_key": pdf_report_r2_key,
            "pdf_local_path": pdf_local_path,
        }
        if existing is not None:
            return await self.update(existing, **payload)
        return await self.create(submission_id=submission_id, **payload)

    async def list_user_scores(
        self,
        user_id: int,
        exam_type: ExamType | None = None,
        limit: int = 20,
    ) -> Sequence[ExamScore]:
        """List historical exam scores for a user ordered from newest to oldest."""
        stmt = select(ExamScore).where(ExamScore.user_id == user_id)
        if exam_type is not None:
            stmt = stmt.where(ExamScore.exam_type == exam_type)
        stmt = stmt.order_by(ExamScore.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_pdf_paths(
        self,
        score_id: int,
        *,
        pdf_local_path: str | None = None,
        pdf_report_r2_key: str | None = None,
    ) -> ExamScore | None:
        """Update local path and Cloudflare R2 object key after PDF report generation."""
        score = await self.get_by_id(score_id)
        if score is None:
            return None
        update_fields: dict[str, Any] = {}
        if pdf_local_path is not None:
            update_fields["pdf_local_path"] = pdf_local_path
        if pdf_report_r2_key is not None:
            update_fields["pdf_report_r2_key"] = pdf_report_r2_key
        return await self.update(score, **update_fields)
