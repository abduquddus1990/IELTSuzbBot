"""Daily usage quotas (free tier: N AI-scored exams per person per day).

Counters live in PostgreSQL when `DATABASE_URL` points to a reachable database (recommended on
Render, whose disk is wiped on every restart); otherwise in a local JSON file, which is fine for
development but resets whenever a cloud instance restarts.

Identity: a verified Telegram user id when available, otherwise the browser's client id. Browser
users are also capped per IP address (more generously, since schools and offices share an IP).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from app.core.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

TASHKENT_TZ = timezone(timedelta(hours=5))

# kind -> how many per day
EXAM = "exam"
TRANSCRIBE = "transcribe"


def today_key() -> str:
    return datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d")


def limit_for(kind: str, subject: str) -> int:
    if kind == EXAM:
        return settings.DAILY_EXAM_LIMIT * (settings.IP_LIMIT_MULTIPLIER if subject.startswith("ip:") else 1)
    return settings.DAILY_TRANSCRIBE_LIMIT * (settings.IP_LIMIT_MULTIPLIER if subject.startswith("ip:") else 1)


class _Store(Protocol):
    async def get(self, day: str, kind: str, subject: str) -> int: ...
    async def add(self, day: str, kind: str, subject: str, delta: int) -> int: ...
    async def totals(self, day: str) -> dict[str, int]: ...


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()

    def _load(self) -> dict[str, dict[str, int]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    async def get(self, day: str, kind: str, subject: str) -> int:
        return self._load().get(day, {}).get(f"{kind}|{subject}", 0)

    async def add(self, day: str, kind: str, subject: str, delta: int) -> int:
        async with self._lock:
            data = {d: v for d, v in self._load().items() if d >= (datetime.now(TASHKENT_TZ) - timedelta(days=7)).strftime("%Y-%m-%d")}
            bucket = data.setdefault(day, {})
            key = f"{kind}|{subject}"
            bucket[key] = max(0, bucket.get(key, 0) + delta)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data), encoding="utf-8")
            return bucket[key]

    async def totals(self, day: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for key, val in self._load().get(day, {}).items():
            kind, subject = key.split("|", 1)
            if not subject.startswith("ip:"):
                out[kind] = out.get(kind, 0) + val
                out[f"{kind}_people"] = out.get(f"{kind}_people", 0) + 1
        return out


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn.replace("postgresql+asyncpg://", "postgresql://").replace("ssl=require", "sslmode=require")
        self._pool = None
        self._lock = asyncio.Lock()

    async def _get_pool(self):
        async with self._lock:
            if self._pool is None:
                import asyncpg

                self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=3, command_timeout=10)
                async with self._pool.acquire() as con:
                    await con.execute(
                        """CREATE TABLE IF NOT EXISTS usage_counters (
                            day date NOT NULL, kind text NOT NULL, subject text NOT NULL,
                            count integer NOT NULL DEFAULT 0, PRIMARY KEY (day, kind, subject))"""
                    )
            return self._pool

    async def get(self, day: str, kind: str, subject: str) -> int:
        pool = await self._get_pool()
        val = await pool.fetchval(
            "SELECT count FROM usage_counters WHERE day=$1 AND kind=$2 AND subject=$3", date.fromisoformat(day), kind, subject
        )
        return int(val or 0)

    async def add(self, day: str, kind: str, subject: str, delta: int) -> int:
        pool = await self._get_pool()
        val = await pool.fetchval(
            """INSERT INTO usage_counters (day, kind, subject, count) VALUES ($1, $2, $3, GREATEST($4::int, 0))
               ON CONFLICT (day, kind, subject) DO UPDATE SET count = GREATEST(usage_counters.count + $4::int, 0)
               RETURNING count""",
            date.fromisoformat(day), kind, subject, delta,
        )
        return int(val)

    async def totals(self, day: str) -> dict[str, int]:
        pool = await self._get_pool()
        rows = await pool.fetch(
            """SELECT kind, SUM(count) AS total, COUNT(*) AS people FROM usage_counters
               WHERE day=$1 AND subject NOT LIKE 'ip:%' GROUP BY kind""",
            date.fromisoformat(day),
        )
        out: dict[str, int] = {}
        for r in rows:
            out[r["kind"]] = int(r["total"])
            out[f"{r['kind']}_people"] = int(r["people"])
        return out


class ResilientStore:
    """Use PostgreSQL, but fall back to the local file if the database is unreachable."""

    def __init__(self, primary: PostgresStore, fallback: JsonStore) -> None:
        self.primary, self.fallback = primary, fallback
        self._failed = False

    async def _call(self, name: str, *args):
        if not self._failed:
            try:
                return await getattr(self.primary, name)(*args)
            except Exception as exc:
                self._failed = True
                logger.error("Usage-limit database unavailable (%s); using local file counters.", exc)
        return await getattr(self.fallback, name)(*args)

    async def get(self, day: str, kind: str, subject: str) -> int:
        return await self._call("get", day, kind, subject)

    async def add(self, day: str, kind: str, subject: str, delta: int) -> int:
        return await self._call("add", day, kind, subject, delta)

    async def totals(self, day: str) -> dict[str, int]:
        return await self._call("totals", day)


def _make_store() -> _Store:
    url = settings.DATABASE_URL.strip()
    local = JsonStore(BASE_DIR / "storage" / "usage_counters.json")
    if url.startswith("postgres") and "localhost" not in url and "127.0.0.1" not in url:
        return ResilientStore(PostgresStore(url), local)
    return local


_store: _Store | None = None


def get_store() -> _Store:
    global _store
    if _store is None:
        _store = _make_store()
    return _store


def set_store(store: _Store) -> None:
    """Swap the backing store (tests)."""
    global _store
    _store = store


@dataclass
class QuotaDecision:
    allowed: bool
    used: int
    limit: int

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)


async def remaining(kind: str, subjects: list[str]) -> QuotaDecision:
    """Quota of the primary subject (subjects[0]); not allowed if any subject is exhausted."""
    day = today_key()
    store = get_store()
    primary_limit = limit_for(kind, subjects[0])
    primary_used = await store.get(day, kind, subjects[0])
    allowed = primary_used < primary_limit
    for subject in subjects[1:]:
        if await store.get(day, kind, subject) >= limit_for(kind, subject):
            allowed = False
    return QuotaDecision(allowed, primary_used if allowed else max(primary_used, primary_limit), primary_limit)


async def consume(kind: str, subjects: list[str]) -> QuotaDecision:
    """Atomically-enough take one unit for every subject; roll back if any is over its limit."""
    day = today_key()
    store = get_store()
    taken: list[str] = []
    primary_used = 0
    for subject in subjects:
        new_val = await store.add(day, kind, subject, 1)
        taken.append(subject)
        if subject == subjects[0]:
            primary_used = new_val
        if new_val > limit_for(kind, subject):
            for s in taken:
                await store.add(day, kind, s, -1)
            primary_limit = limit_for(kind, subjects[0])
            return QuotaDecision(False, primary_limit, primary_limit)
    return QuotaDecision(True, primary_used, limit_for(kind, subjects[0]))


async def refund(kind: str, subjects: list[str]) -> None:
    """Give a unit back (the AI failed, so the attempt should not count)."""
    day = today_key()
    for subject in subjects:
        try:
            await get_store().add(day, kind, subject, -1)
        except Exception as exc:  # pragma: no cover
            logger.warning("Quota refund failed for %s: %s", subject, exc)


async def daily_totals() -> dict[str, int]:
    return await get_store().totals(today_key())
