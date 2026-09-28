"""SQLAlchemy 2.0 ORM models and domain enumerations registry.

Importing `app.models` registers all tables with `Base.metadata` for Alembic migrations.
"""

from app.models.enums import (
    CEFRLevel,
    ExamType,
    PaymentProvider,
    PaymentStatus,
    SubmissionStatus,
)
from app.models.score import ExamScore
from app.models.submission import TestSubmission
from app.models.test import MockTest
from app.models.user import PaymentTransaction, User

__all__ = [
    "CEFRLevel",
    "ExamScore",
    "ExamType",
    "MockTest",
    "PaymentProvider",
    "PaymentStatus",
    "PaymentTransaction",
    "SubmissionStatus",
    "TestSubmission",
    "User",
]
