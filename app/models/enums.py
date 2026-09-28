"""Domain enumerations for IELTS & CEFR Mock AI models and schemas."""

from enum import StrEnum


class ExamType(StrEnum):
    """Supported standardized language examination types."""

    IELTS = "IELTS"
    CEFR = "CEFR"


class CEFRLevel(StrEnum):
    """Common European Framework of Reference for Languages (CEFR) proficiency levels."""

    BELOW_B1 = "BELOW_B1"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"


class SubmissionStatus(StrEnum):
    """Lifecycle states of a candidate's mock test submission."""

    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    FLAGGED_CHEATING = "FLAGGED_CHEATING"


class PaymentProvider(StrEnum):
    """Supported payment providers and credit sources in Uzbekistan."""

    CLICK = "CLICK"
    PAYME = "PAYME"
    BONUS = "BONUS"


class PaymentStatus(StrEnum):
    """Transaction statuses for Click and Payme merchant callbacks."""

    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
