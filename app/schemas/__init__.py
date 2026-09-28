"""Pydantic v2 schema exports for the IELTS & CEFR Mock AI platform."""

from app.schemas.writing import (
    BandBoosterItem,
    BandBoosterVocabulary,
    CEFRLevel,
    CriteriaScores,
    DetailedError,
    DetailedErrorItem,
    ExamType,
    ImageMediaType,
    VisionOCRResult,
    WritingEvaluationRequest,
    WritingEvaluationResult,
    WritingTaskInput,
)
from app.schemas.speaking import (
    AudioTranscriptionResult,
    SpeakingCriteriaScores,
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
    SpeakingPartInput,
)
from app.schemas.report import (
    FullExamReportData,
    SectionScoreSummary,
    band_to_cefr_75_score,
)

__all__ = [
    "AudioTranscriptionResult",
    "BandBoosterItem",
    "BandBoosterVocabulary",
    "CEFRLevel",
    "CriteriaScores",
    "DetailedError",
    "DetailedErrorItem",
    "ExamType",
    "FullExamReportData",
    "ImageMediaType",
    "SectionScoreSummary",
    "SpeakingCriteriaScores",
    "SpeakingEvaluationRequest",
    "SpeakingEvaluationResult",
    "SpeakingPartInput",
    "VisionOCRResult",
    "WritingEvaluationRequest",
    "WritingEvaluationResult",
    "WritingTaskInput",
    "band_to_cefr_75_score",
]
