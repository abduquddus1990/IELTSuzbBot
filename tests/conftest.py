"""Shared pytest configuration: isolate on-disk state so tests never touch real data."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.services import payment_service, usage_limits

# Tests exercise the offline demo evaluators when live AI keys are absent or fail.
settings.ALLOW_DEMO_AI_FALLBACK = True


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path, monkeypatch):
    """Per-test usage counters and billing ledger in a temp dir; generous limits by default."""
    usage_limits.set_store(usage_limits.JsonStore(tmp_path / "usage.json"))
    monkeypatch.setattr(payment_service, "_billing_ledger_singleton", payment_service.BillingLedgerService(ledger_path=tmp_path / "ledger.json"))
    monkeypatch.setattr(settings, "DAILY_EXAM_LIMIT", 100)
    yield
    usage_limits.set_store(None)  # type: ignore[arg-type]
