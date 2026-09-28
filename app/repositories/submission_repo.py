"""Repository for managing candidate TestSubmission lifecycles and 4-skill answers."""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ExamType, SubmissionStatus
from app.models.submission import TestSubmission
from app.repositories.base import BaseRepository


class SubmissionRepository(BaseRepository[TestSubmission]):
    """Asynchronous data access layer for `TestSubmission` records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=TestSubmission)

    async def create_submission(
        self,
        user_id: int,
        test_id: int,
        exam_type: ExamType,
    ) -> TestSubmission:
        """Start a new mock exam attempt in `IN_PROGRESS` status."""
        return await self.create(
            user_id=user_id,
            test_id=test_id,
            exam_type=exam_type,
            status=SubmissionStatus.IN_PROGRESS,
            listening_answers={},
            reading_answers={},
            speaking_audio_r2_keys={},
            speaking_transcripts={},
            anti_cheat_flags={},
        )

    async def get_with_details(self, submission_id: int) -> TestSubmission | None:
        """Fetch a submission along with its related `test`, `user`, and `score` entities."""
        stmt = (
            select(TestSubmission)
            .options(
                selectinload(TestSubmission.test),
                selectinload(TestSubmission.user),
                selectinload(TestSubmission.score),
            )
            .where(TestSubmission.id == submission_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_submissions(
        self,
        user_id: int,
        exam_type: ExamType | None = None,
        limit: int = 20,
    ) -> Sequence[TestSubmission]:
        """List recent test submissions for a candidate, ordered newest first."""
        stmt = (
            select(TestSubmission)
            .options(selectinload(TestSubmission.score), selectinload(TestSubmission.test))
            .where(TestSubmission.user_id == user_id)
        )
        if exam_type is not None:
            stmt = stmt.where(TestSubmission.exam_type == exam_type)
        stmt = stmt.order_by(TestSubmission.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_objective_answers(
        self,
        submission_id: int,
        *,
        listening_answers: dict[str, Any] | None = None,
        reading_answers: dict[str, Any] | None = None,
    ) -> TestSubmission | None:
        """Persist candidate's Listening and/or Reading question responses."""
        submission = await self.get_by_id(submission_id)
        if submission is None:
            return None
        if listening_answers is not None:
            submission.listening_answers = listening_answers
        if reading_answers is not None:
            submission.reading_answers = reading_answers
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission

    async def save_writing_submission(
        self,
        submission_id: int,
        *,
        task_1_text: str | None = None,
        task_2_text: str | None = None,
        task_1_image_r2_key: str | None = None,
        task_2_image_r2_key: str | None = None,
        is_ocr_used: bool = False,
    ) -> TestSubmission | None:
        """Persist candidate's Writing Task 1 & Task 2 essays and optional OCR image R2 keys."""
        submission = await self.get_by_id(submission_id)
        if submission is None:
            return None
        if task_1_text is not None:
            submission.writing_task_1_text = task_1_text
        if task_2_text is not None:
            submission.writing_task_2_text = task_2_text
        if task_1_image_r2_key is not None:
            submission.writing_task_1_image_r2_key = task_1_image_r2_key
        if task_2_image_r2_key is not None:
            submission.writing_task_2_image_r2_key = task_2_image_r2_key
        submission.is_ocr_used = is_ocr_used

        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission

    async def save_speaking_submission(
        self,
        submission_id: int,
        *,
        audio_r2_keys: dict[str, Any] | None = None,
        transcripts: dict[str, Any] | None = None,
    ) -> TestSubmission | None:
        """Persist Cloudflare R2 voice recording keys and OpenAI Whisper STT transcripts."""
        submission = await self.get_by_id(submission_id)
        if submission is None:
            return None
        if audio_r2_keys is not None:
            submission.speaking_audio_r2_keys = audio_r2_keys
        if transcripts is not None:
            submission.speaking_transcripts = transcripts

        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission

    async def update_status(
        self,
        submission_id: int,
        status: SubmissionStatus,
        *,
        anti_cheat_flags: dict[str, Any] | None = None,
    ) -> TestSubmission | None:
        """Transition submission status and record completion timestamp if finished."""
        submission = await self.get_by_id(submission_id)
        if submission is None:
            return None

        submission.status = status
        if status in (
            SubmissionStatus.COMPLETED,
            SubmissionStatus.FAILED,
            SubmissionStatus.FLAGGED_CHEATING,
        ):
            submission.completed_at = datetime.now(timezone.utc)
        if anti_cheat_flags is not None:
            merged_flags = dict(submission.anti_cheat_flags or {})
            merged_flags.update(anti_cheat_flags)
            submission.anti_cheat_flags = merged_flags

        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission
