"""TestSubmission SQLAlchemy 2.0 ORM model capturing candidate exam attempts and answers."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ExamType, SubmissionStatus

if TYPE_CHECKING:
    from app.models.score import ExamScore
    from app.models.test import MockTest
    from app.models.user import User


class TestSubmission(Base, TimestampMixin):
    """Represents a user's attempt at a MockTest across all 4 language skills."""

    __tablename__ = "test_submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("mock_tests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(ExamType, name="exam_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status_enum"),
        default=SubmissionStatus.IN_PROGRESS,
        server_default=SubmissionStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Objective Sections (Deterministic Python Scoring)
    listening_answers: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    reading_answers: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Writing Section (Text + Optional Handwritten Image OCR)
    writing_task_1_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    writing_task_1_image_r2_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    writing_task_2_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    writing_task_2_image_r2_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    is_ocr_used: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Speaking Section (Cloudflare R2 Audio Keys + Whisper Transcripts)
    speaking_audio_r2_keys: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    speaking_transcripts: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Security & Telemetry (Tab switches, clipboard paste events, prompt injection flags)
    anti_cheat_flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="submissions")
    test: Mapped[MockTest] = relationship("MockTest", back_populates="submissions")
    score: Mapped[ExamScore | None] = relationship(
        "ExamScore",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<TestSubmission(id={self.id}, user_id={self.user_id}, "
            f"test_id={self.test_id}, exam_type={self.exam_type}, status={self.status})>"
        )
