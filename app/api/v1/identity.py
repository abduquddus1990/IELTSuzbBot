"""Who is calling: verified Telegram user, or an anonymous browser client (+ IP)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from fastapi import Request

from app.core.config import settings
from app.utils.telegram_auth import verify_telegram_webapp_init_data

_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


@dataclass
class Caller:
    subjects: list[str]
    telegram_user: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def telegram_id(self) -> int | None:
        if self.telegram_user and isinstance(self.telegram_user.get("id"), int):
            return self.telegram_user["id"]
        return None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def resolve_caller(request: Request) -> Caller:
    init_data = request.headers.get("x-telegram-init-data", "").strip()
    if init_data:
        try:
            verified = verify_telegram_webapp_init_data(init_data, bot_token=settings.BOT_TOKEN)
            user = verified.get("user") or {}
            if isinstance(user.get("id"), int):
                return Caller(subjects=[f"tg:{user['id']}"], telegram_user=user)
        except ValueError:
            pass
    ip_subject = f"ip:{client_ip(request)}"
    client_id = request.headers.get("x-client-id", "").strip()
    if _CLIENT_ID_RE.match(client_id):
        return Caller(subjects=[f"web:{client_id}", ip_subject])
    return Caller(subjects=[ip_subject])
