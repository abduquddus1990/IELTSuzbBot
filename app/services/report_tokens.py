"""Signed, compressed report tokens.

The free Render instance loses `storage/reports/*.pdf` on every restart. Instead of a database,
the full report data is signed with `SECRET_KEY` and returned to the client; the PDF download URL
carries the token, so the server can regenerate the exact same PDF at any time while candidates
cannot forge scores.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import zlib
from typing import Any

from app.core.config import settings


def _sign(payload: bytes) -> bytes:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).digest()[:16]


def encode_report_token(report_data: dict[str, Any]) -> str:
    raw = zlib.compress(json.dumps(report_data, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), 9)
    return base64.urlsafe_b64encode(_sign(raw) + raw).decode("ascii").rstrip("=")


def decode_report_token(token: str) -> dict[str, Any]:
    try:
        blob = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    except (ValueError, TypeError) as exc:
        raise ValueError("Malformed report token.") from exc
    sig, raw = blob[:16], blob[16:]
    if len(sig) != 16 or not hmac.compare_digest(sig, _sign(raw)):
        raise ValueError("Invalid report token signature.")
    return json.loads(zlib.decompress(raw).decode("utf-8"))
