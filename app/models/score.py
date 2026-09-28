"""ExamScore SQLAlchemy 2.0 ORM model storing final scores, AI diagnostics, and PDF report keys."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CEFRLevel, ExamType

if TYPE_CHECKING:
    from app.models.submission import TestSubmission
    from app.models.user import User


class ExamScore(Base, TimestampMixin):
    """Comprehensive score breakdown, AI feedback, and PDF report locations for a TestSubmission."""

    __tablename__ = "exam_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(ExamType, name="exam_type_enum", create_type=False),
        nullable=False,
        index=True,
    )

    # Objective Section Scores
    listening_raw: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    listening_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )
    reading_raw: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    reading_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )

    # Writing & Speaking Section Scores
    writing_task_1_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )
    writing_task_2_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )
    writing_overall_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )
    speaking_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )

    # Overall Result & CEFR Equivalence
    overall_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False, index=True
    )
    cefr_level: Mapped[CEFRLevel] = mapped_column(
        Enum(CEFRLevel, name="cefr_level_enum"),
        default=CEFRLevel.BELOW_B1,
        server_default=CEFRLevel.BELOW_B1.value,
        nullable=False,
        index=True,
    )

    # Structured AI Evaluation Rubrics & Error Analysis
    writing_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    writing_detailed_errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    writing_band_booster: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    speaking_feedback: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # AI Cost & Token Telemetry
    ai_tokens_used: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    ai_cost_usd: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0", nullable=False
    )

    # Generated PDF Report Storage
    pdf_report_r2_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_local_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    submission: Mapped[TestSubmission] = relationship(
        "TestSubmission", back_populates="score"
    )
    user: Mapped[User] = relationship("User", back_populates="scores")

    def __repr__(self) -> str:
        return (
            f"<ExamScore(id={self.id}, submission_id={self.submission_id}, "
            f"exam_type={self.exam_type}, overall_score={self.overall_score}, "
            f"cefr_level={self.cefr_level})>"
        )
