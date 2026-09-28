"""Telegram WebApp (Mini App) HMAC-SHA256 `initData` Authentication & Signing Utility.

Implements the official Telegram Mini Apps validation algorithm:
1. `secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token.encode("utf-8")).digest()`
2. `data_check_string` = all query parameters (except `hash`) sorted alphabetically by key,
   formatted as `key=value` and joined by `\\n`.
3. `computed_hash = HMAC_SHA256(key=secret_key, msg=data_check_string.encode("utf-8")).hexdigest()`
4. Constant-time comparison via `hmac.compare_digest(computed_hash, provided_hash)` and
   freshness verification of `auth_date`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl, urlencode

from app.core.config import settings


def compute_webapp_secret_key(bot_token: str) -> bytes:
    """Compute the HMAC-SHA256 secret key for Telegram WebApp data verification."""
    if not bot_token or not bot_token.strip():
        raise ValueError("bot_token cannot be empty.")
    return hmac.new(
        key=b"WebAppData",
        msg=bot_token.strip().encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()


def create_signed_webapp_init_data(
    user_data: dict[str, Any],
    bot_token: str | None = None,
    auth_date: int | None = None,
    query_id: str = "AAHdF6IQAAAAAN0XohDhrOrc",
) -> str:
    """Build a cryptographically signed Telegram WebApp `initData` query string.

    Useful for end-to-end testing and simulating authenticated Mini App requests.
    """
    if not isinstance(user_data, dict) or not user_data:
        raise ValueError("user_data must be a non-empty dictionary.")

    resolved_token = (bot_token if bot_token is not None else settings.BOT_TOKEN).strip()
    if not resolved_token:
        raise ValueError("bot_token cannot be empty.")

    resolved_auth_date = int(auth_date) if auth_date is not None else int(time.time())
    user_json = json.dumps(user_data, separators=(",", ":"), ensure_ascii=False)

    params: dict[str, str] = {
        "auth_date": str(resolved_auth_date),
        "query_id": query_id,
        "user": user_json,
    }

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items(), key=lambda item: item[0])
    )
    secret_key = compute_webapp_secret_key(resolved_token)
    signature = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    signed_params = {**params, "hash": signature}
    return urlencode(signed_params)


def verify_telegram_webapp_init_data(
    init_data: str,
    bot_token: str | None = None,
    max_age_seconds: int = 86400,
) -> dict[str, Any]:
    """Verify a Telegram WebApp `initData` query string using HMAC-SHA256.

    Raises:
        ValueError: If `init_data` is empty, missing `hash` or `auth_date`, has a
            tampered/invalid HMAC signature, has expired beyond `max_age_seconds`,
            or contains malformed `user` JSON.

    Returns:
        A dictionary containing the verified payload including `"user"` (parsed dict),
        `"auth_date"` (int), and `"hash"` (str).
    """
    if not init_data or not isinstance(init_data, str) or not init_data.strip():
        raise ValueError("Telegram WebApp initData cannot be empty.")

    resolved_token = (bot_token if bot_token is not None else settings.BOT_TOKEN).strip()
    if not resolved_token:
        raise ValueError("Bot token is required to verify Telegram WebApp initData.")

    raw_pairs = parse_qsl(init_data.strip(), keep_blank_values=True)
    if not raw_pairs:
        raise ValueError("Malformed Telegram WebApp initData query string.")

    provided_hash: str | None = None
    check_pairs: list[tuple[str, str]] = []
    parsed_dict: dict[str, Any] = {}

    for key, value in raw_pairs:
        if key == "hash":
            provided_hash = value.strip()
        else:
            check_pairs.append((key, value))
            parsed_dict[key] = value

    if not provided_hash:
        raise ValueError("Missing 'hash' parameter in Telegram WebApp initData.")

    if "auth_date" not in parsed_dict:
        raise ValueError("Missing 'auth_date' parameter in Telegram WebApp initData.")

    try:
        auth_date_int = int(str(parsed_dict["auth_date"]).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid 'auth_date' timestamp in Telegram WebApp initData.") from exc

    # Reconstruct the canonical alphabetical data_check_string
    check_pairs.sort(key=lambda item: item[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in check_pairs)

    secret_key = compute_webapp_secret_key(resolved_token)
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash.lower(), provided_hash.lower()):
        raise ValueError("Invalid Telegram WebApp initData HMAC-SHA256 signature.")

    if max_age_seconds > 0:
        now_ts = int(time.time())
        age = now_ts - auth_date_int
        if age > max_age_seconds:
            raise ValueError(
                f"Telegram WebApp initData has expired (age={age}s > max_age_seconds={max_age_seconds}s)."
            )
        if auth_date_int > now_ts + 300:
            raise ValueError("Telegram WebApp initData auth_date is in the future.")

    parsed_user: dict[str, Any] = {}
    if "user" in parsed_dict:
        try:
            user_obj = json.loads(parsed_dict["user"])
            if not isinstance(user_obj, dict):
                raise ValueError("Parsed 'user' field is not a JSON object.")
            parsed_user = user_obj
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("Malformed 'user' JSON in Telegram WebApp initData.") from exc

    result: dict[str, Any] = {
        **parsed_dict,
        "auth_date": auth_date_int,
        "user": parsed_user,
        "hash": provided_hash,
    }
    return result


__all__ = [
    "compute_webapp_secret_key",
    "create_signed_webapp_init_data",
    "verify_telegram_webapp_init_data",
]
