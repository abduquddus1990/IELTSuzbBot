"""MockTest SQLAlchemy 2.0 ORM model storing IELTS & CEFR 4-skill test content."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, Enum, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ExamType

if TYPE_CHECKING:
    from app.models.submission import TestSubmission


class MockTest(Base, TimestampMixin):
    """Structured IELTS or CEFR Mock Exam containing Listening, Reading, Writing, and Speaking sections.

    JSONB column structures:
    - `listening_data`: {
        "audio_r2_key": "listening/test_01.mp3",
        "duration_minutes": 30,
        "questions": [...],
        "answer_key": {"1": "library", "2": ["A", "first floor"], ...}
      }
    - `reading_data`: {
        "duration_minutes": 60,
        "passages": [{"id": 1, "title": "...", "content": "..."}],
        "questions": [...],
        "answer_key": {"1": "TRUE", "2": "NOT GIVEN", ...}
      }
    - `writing_data`: {
        "task_1_prompt": "...",
        "task_1_image_r2_key": "writing/test_01_chart.png",
        "task_2_prompt": "...",
        "min_words_t1": 150,
        "min_words_t2": 250
      }
    - `speaking_data`: {
        "part_1_questions": ["...", "..."],
        "part_2_cue_card": {"topic": "...", "bullets": ["...", "..."]},
        "part_3_questions": ["...", "..."]
      }
    """

    __tablename__ = "mock_tests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    exam_type: Mapped[ExamType] = mapped_column(
        Enum(ExamType, name="exam_type_enum", create_type=False),
        nullable=False,
        index=True,
    )
    version_code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, default=165, server_default="165", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, index=True
    )
    is_free_trial: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False, index=True
    )

    listening_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    reading_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    writing_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    speaking_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Relationships
    submissions: Mapped[list[TestSubmission]] = relationship(
        "TestSubmission",
        back_populates="test",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MockTest(id={self.id}, version_code={self.version_code!r}, "
            f"exam_type={self.exam_type}, is_active={self.is_active})>"
        )
