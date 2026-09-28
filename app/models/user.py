"""User and PaymentTransaction SQLAlchemy 2.0 ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ExamType, PaymentProvider, PaymentStatus

if TYPE_CHECKING:
    from app.models.score import ExamScore
    from app.models.submission import TestSubmission


class User(Base, TimestampMixin):
    """Registered Telegram candidate profile, wallet balance, and exam targets."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language_code: Mapped[str] = mapped_column(
        String(10), default="uz", server_default="uz", nullable=False
    )

    target_exam: Mapped[ExamType] = mapped_column(
        Enum(ExamType, name="exam_type_enum"),
        default=ExamType.IELTS,
        server_default=ExamType.IELTS.value,
        nullable=False,
    )
    target_band: Mapped[float | None] = mapped_column(Float, nullable=True, default=7.0)

    balance_uzs: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", nullable=False
    )
    free_credits: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Relationships
    submissions: Mapped[list[TestSubmission]] = relationship(
        "TestSubmission",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    scores: Mapped[list[ExamScore]] = relationship(
        "ExamScore",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    transactions: Mapped[list[PaymentTransaction]] = relationship(
        "PaymentTransaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"target_exam={self.target_exam}, balance_uzs={self.balance_uzs})>"
        )


class PaymentTransaction(Base, TimestampMixin):
    """Financial transaction ledger for Click, Payme, and promotional bonus top-ups."""

    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider_enum"),
        nullable=False,
        index=True,
    )
    provider_tx_id: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    amount_uzs: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return (
            f"<PaymentTransaction(id={self.id}, user_id={self.user_id}, "
            f"provider={self.provider}, amount_uzs={self.amount_uzs}, status={self.status})>"
        )
