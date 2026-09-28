"""Repository for querying and managing MockTest records."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExamType
from app.models.test import MockTest
from app.repositories.base import BaseRepository


class MockTestRepository(BaseRepository[MockTest]):
    """Asynchronous data access layer for `MockTest` exam papers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=MockTest)

    async def get_by_version_code(self, version_code: str) -> MockTest | None:
        """Retrieve a mock test by its unique version code (e.g., 'IELTS-MOCK-001')."""
        stmt = select(MockTest).where(MockTest.version_code == version_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_by_exam_type(
        self,
        exam_type: ExamType,
        *,
        free_trial_only: bool = False,
    ) -> Sequence[MockTest]:
        """List all active mock tests filtered by `ExamType` (IELTS or CEFR)."""
        stmt = select(MockTest).where(
            MockTest.exam_type == exam_type,
            MockTest.is_active.is_(True),
        )
        if free_trial_only:
            stmt = stmt.where(MockTest.is_free_trial.is_(True))
        stmt = stmt.order_by(MockTest.id.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_free_trial_test(self, exam_type: ExamType) -> MockTest | None:
        """Return the primary active free trial mock test for the given exam type."""
        stmt = (
            select(MockTest)
            .where(
                MockTest.exam_type == exam_type,
                MockTest.is_active.is_(True),
                MockTest.is_free_trial.is_(True),
            )
            .order_by(MockTest.id.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
