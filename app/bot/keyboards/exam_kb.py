"""Inline keyboards for the IELTS & CEFR Mock AI Telegram bot (`aiogram 3.x`)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.core.config import settings


def _read_live_env_webapp_url() -> str | None:
    """Read the latest WEBAPP_URL directly from cloud platform env vars or `.env`."""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if render_url:
        return f"{render_url.rstrip('/')}/webapp/"
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain.removeprefix('https://').rstrip('/')}/webapp/"

    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return None
    try:
        content = env_path.read_text(encoding="utf-8")
        match = re.search(r'^WEBAPP_URL\s*=\s*["\']?([^"\'\r\n]+)["\']?', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        return None
    return None


def _resolve_webapp_url(webapp_url: str | None = None, exam_type: str | None = None) -> str:
    """Resolve the Mini App URL and optionally append `?exam_type=...`."""
    base_url = (webapp_url or _read_live_env_webapp_url() or settings.WEBAPP_URL or "https://app.yourdomain.uz").strip()
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url.lstrip('/')}"
    if exam_type:
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}exam_type={exam_type.strip().upper()}"
    return base_url


def _is_public_https_url(url: str) -> bool:
    """Telegram only accepts public HTTPS URLs for WebApp buttons."""
    lower = url.lower().strip()
    if not lower.startswith("https://"):
        return False
    return not any(host in lower for host in ("localhost", "127.0.0.1", "0.0.0.0"))


def _build_webapp_inline_button(text: str, resolved_url: str) -> InlineKeyboardButton:
    if _is_public_https_url(resolved_url):
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=resolved_url))
    return InlineKeyboardButton(text=text, callback_data="menu:webapp_local")


def build_main_menu_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    resolved_url = _resolve_webapp_url(webapp_url)
    rows: list[list[InlineKeyboardButton]] = [
        [_build_webapp_inline_button(text="📝 Full mock exam (all 4 skills)", resolved_url=resolved_url)],
        [
            InlineKeyboardButton(text="🇬🇧 IELTS practice", callback_data="exam_type:IELTS"),
            InlineKeyboardButton(text="🇺🇿 CEFR practice", callback_data="exam_type:CEFR"),
        ],
    ]
    if _is_public_https_url(resolved_url):
        rows.append([InlineKeyboardButton(text="💻 Open on a computer (browser)", url=resolved_url)])
    rows.append([InlineKeyboardButton(text="ℹ️ Help / Yordam", callback_data="menu:help")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_exam_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇬🇧 IELTS Academic (Band 0–9)", callback_data="exam_type:IELTS")],
            [InlineKeyboardButton(text="🇺🇿 Multilevel CEFR (0–75, B1–C1)", callback_data="exam_type:CEFR")],
        ]
    )


def build_exam_mode_keyboard(exam_type: str, webapp_url: str | None = None) -> InlineKeyboardMarkup:
    norm_type = (exam_type or "IELTS").strip().upper()
    if norm_type not in {"IELTS", "CEFR"}:
        norm_type = "IELTS"
    resolved_url = _resolve_webapp_url(webapp_url, exam_type=norm_type)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_build_webapp_inline_button(text=f"📝 Full {norm_type} mock (Mini App)", resolved_url=resolved_url)],
            [InlineKeyboardButton(text="✍️ Writing practice (Task 1 + 2)", callback_data="mode:writing")],
            [InlineKeyboardButton(text="🎙 Speaking practice (voice, Parts 1–3)", callback_data="mode:speaking")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="menu:choose_exam")],
        ]
    )


__all__ = [
    "build_exam_mode_keyboard",
    "build_exam_type_keyboard",
    "build_main_menu_keyboard",
]
