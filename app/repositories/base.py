"""Generic asynchronous Repository Pattern base class for SQLAlchemy 2.0 ORM models."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing standard asynchronous CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """Initialize repository with an active SQLAlchemy AsyncSession and ORM model class."""
        self.session = session
        self.model = model

    async def get_by_id(self, record_id: int) -> ModelType | None:
        """Retrieve a single record by its primary key ID."""
        stmt = select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, offset: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Retrieve a paginated list of records."""
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Return total count of records in the table."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **kwargs: Any) -> ModelType:
        """Instantiate, persist, and refresh a new model record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """Update attributes on an existing model instance and commit changes."""
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a model instance from the database and commit."""
        await self.session.delete(instance)
        await self.session.commit()
