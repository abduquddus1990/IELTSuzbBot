"""Repository for User profile, wallet balance, and Click/Payme payment transactions."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExamType, PaymentProvider, PaymentStatus
from app.models.user import PaymentTransaction, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Asynchronous data access layer for `User` and `PaymentTransaction` models."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch a user by their unique Telegram user ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_telegram_user(
        self,
        telegram_id: int,
        full_name: str,
        username: str | None = None,
        language_code: str = "uz",
        free_credits: int = 1,
        is_admin: bool = False,
    ) -> tuple[User, bool]:
        """Retrieve an existing user by Telegram ID or create a new profile.

        Returns:
            A tuple of `(user, created)` where `created` is True if newly registered.
        """
        existing = await self.get_by_telegram_id(telegram_id)
        if existing is not None:
            updated = False
            if username and existing.username != username:
                existing.username = username
                updated = True
            if full_name and existing.full_name != full_name:
                existing.full_name = full_name
                updated = True
            if updated:
                await self.session.commit()
                await self.session.refresh(existing)
            return existing, False

        new_user = await self.create(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            language_code=language_code,
            free_credits=free_credits,
            is_admin=is_admin,
        )
        return new_user, True

    async def update_target_exam(
        self,
        user_id: int,
        target_exam: ExamType,
        target_band: float | None = None,
    ) -> User | None:
        """Update a candidate's target exam (IELTS or CEFR) and target band score."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        update_data: dict[str, Any] = {"target_exam": target_exam}
        if target_band is not None:
            update_data["target_band"] = target_band
        return await self.update(user, **update_data)

    async def deduct_credit_or_balance(self, user_id: int, price_uzs: int) -> User:
        """Deduct 1 free trial credit if available; otherwise deduct `price_uzs` from wallet.

        Raises:
            ValueError: If user is not found or has insufficient credits and balance.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with id={user_id} does not exist.")

        if user.free_credits > 0:
            user.free_credits -= 1
        elif user.balance_uzs >= price_uzs:
            user.balance_uzs -= price_uzs
        else:
            raise ValueError(
                f"Insufficient balance. Required: {price_uzs} UZS, "
                f"Available: {user.balance_uzs} UZS (Free credits: {user.free_credits})."
            )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def add_balance(self, user_id: int, amount_uzs: int) -> User | None:
        """Credit a user's UZS wallet balance."""
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.balance_uzs += amount_uzs
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_transaction(
        self,
        user_id: int,
        provider: PaymentProvider,
        amount_uzs: int,
        provider_tx_id: str | None = None,
        description: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> PaymentTransaction:
        """Create a new pending payment transaction record."""
        tx = PaymentTransaction(
            user_id=user_id,
            provider=provider,
            provider_tx_id=provider_tx_id,
            amount_uzs=amount_uzs,
            status=PaymentStatus.PENDING,
            description=description,
            raw_payload=raw_payload,
        )
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    async def get_transaction_by_provider_id(
        self, provider: PaymentProvider, provider_tx_id: str
    ) -> PaymentTransaction | None:
        """Find a transaction by payment provider and external merchant transaction ID."""
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.provider == provider,
            PaymentTransaction.provider_tx_id == provider_tx_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_transaction_paid(
        self,
        transaction_id: int,
        provider_tx_id: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> PaymentTransaction | None:
        """Mark a pending transaction as PAID and atomically credit the user's UZS balance."""
        stmt = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        result = await self.session.execute(stmt)
        tx = result.scalar_one_or_none()
        if tx is None:
            return None

        if tx.status == PaymentStatus.PAID:
            return tx

        tx.status = PaymentStatus.PAID
        tx.paid_at = datetime.now(timezone.utc)
        if provider_tx_id is not None:
            tx.provider_tx_id = provider_tx_id
        if raw_payload is not None:
            tx.raw_payload = raw_payload

        user = await self.get_by_id(tx.user_id)
        if user is not None:
            user.balance_uzs += tx.amount_uzs
            self.session.add(user)

        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx
