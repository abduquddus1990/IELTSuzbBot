"""Inline and Reply Keyboards for the IELTS & CEFR Mock AI Telegram Bot (`aiogram 3.x`)."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

import os
from pathlib import Path
import re

from app.core.config import settings


def _read_live_env_webapp_url() -> str | None:
    """Read the latest WEBAPP_URL directly from `.env` or cloud platform env vars."""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if render_url:
        return f"{render_url.rstrip('/')}/webapp"
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain.lstrip('https://').rstrip('/')}/webapp"

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
    """Resolve the Telegram Mini App URL and optionally append `?exam_type=...` query param."""
    base_url = (webapp_url or _read_live_env_webapp_url() or settings.WEBAPP_URL or "https://app.yourdomain.uz").strip()
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url.lstrip('/')}"
    if exam_type:
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}exam_type={exam_type.strip().upper()}"
    return base_url


def _is_public_https_url(url: str) -> bool:
    """Return True if the URL is a public HTTPS URL accepted by Telegram WebAppInfo."""
    lower = url.lower().strip()
    if not lower.startswith("https://"):
        return False
    if "localhost" in lower or "127.0.0.1" in lower or "0.0.0.0" in lower:
        return False
    return True


def _build_webapp_inline_button(text: str, resolved_url: str) -> InlineKeyboardButton:
    """Build a WebApp inline button for public HTTPS URLs, or a local info callback for localhost."""
    if _is_public_https_url(resolved_url):
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=resolved_url))
    return InlineKeyboardButton(text=text, callback_data="menu:webapp_local")


def build_main_menu_keyboard(webapp_url: str | None = None) -> InlineKeyboardMarkup:
    """Build the main welcome menu keyboard with exam type selection and Mini App launcher."""
    resolved_url = _resolve_webapp_url(webapp_url)
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="🇬🇧 IELTS Academic (0.0 - 9.0)",
                callback_data="exam_type:IELTS",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🇺🇿 Milliy CEFR Multi-Level (0 - 75)",
                callback_data="exam_type:CEFR",
            ),
        ],
        [
            _build_webapp_inline_button(
                text="🖥 Interaktiv Mini App (WebApp) ochish",
                resolved_url=resolved_url,
            ),
        ],
        [
            InlineKeyboardButton(
                text="💳 Tarif Sotib Olish (Karta / ⭐ Stars)",
                callback_data="menu:buy",
            ),
        ],
        [
            InlineKeyboardButton(
                text="👤 Profil va Tariflar",
                callback_data="menu:profile",
            ),
            InlineKeyboardButton(
                text="ℹ️ Yordam",
                callback_data="menu:help",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_exam_type_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for choosing between IELTS Academic and Uzbekistan CEFR."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇬🇧 IELTS Academic Mock (Band 0.0 - 9.0)",
                    callback_data="exam_type:IELTS",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🇺🇿 O'zbekiston BBA Multi-Level CEFR (B1-C1 / 0-75)",
                    callback_data="exam_type:CEFR",
                ),
            ],
        ]
    )


def build_exam_mode_keyboard(
    exam_type: str,
    webapp_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Build the exam mode selection keyboard (`mode:full`, `mode:writing`, `mode:speaking` + WebApp)."""
    norm_type = (exam_type or "IELTS").strip().upper()
    if norm_type not in {"IELTS", "CEFR"}:
        norm_type = "IELTS"
    resolved_url = _resolve_webapp_url(webapp_url, exam_type=norm_type)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🏆 To'liq 4-Skill {norm_type} Mock (L+R+W+S)",
                    callback_data="mode:full",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✍️ Faqat Writing (Task 1 + Task 2 + OCR)",
                    callback_data="mode:writing",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎙 Faqat Speaking (Part 1, 2, 3 — Whisper AI)",
                    callback_data="mode:speaking",
                ),
            ],
            [
                _build_webapp_inline_button(
                    text=f"📱 {norm_type} Mini App (Listening/Reading/Writing)",
                    resolved_url=resolved_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Imtihon turini o'zgartirish",
                    callback_data="menu:choose_exam",
                ),
            ],
        ]
    )


def build_listening_reading_keyboard(
    exam_type: str = "IELTS",
    webapp_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Build helper keyboard for the Listening & Reading step (WebApp + quick test score presets)."""
    norm_type = (exam_type or "IELTS").strip().upper()
    resolved_url = _resolve_webapp_url(webapp_url, exam_type=norm_type)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _build_webapp_inline_button(
                    text=f"🎧📖 {norm_type} Listening & Reading Mini App",
                    resolved_url=resolved_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Namuna natija: L=32/40, R=30/40 (Band 7.5 / 7.0)",
                    callback_data="lr_quick:32:30",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Namuna natija: L=26/40, R=24/40 (Band 6.5 / 6.0)",
                    callback_data="lr_quick:26:24",
                ),
            ],
        ]
    )


def build_webapp_reply_keyboard(
    exam_type: str = "IELTS",
    webapp_url: str | None = None,
) -> ReplyKeyboardMarkup:
    """Build a ReplyKeyboardMarkup with a WebApp button that triggers `F.web_app_data` on submit."""
    norm_type = (exam_type or "IELTS").strip().upper()
    resolved_url = _resolve_webapp_url(webapp_url, exam_type=norm_type)
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=f"📱 {norm_type} Listening & Reading Testni Boshlash",
                    web_app=WebAppInfo(url=resolved_url),
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


__all__ = [
    "build_exam_mode_keyboard",
    "build_exam_type_keyboard",
    "build_listening_reading_keyboard",
    "build_main_menu_keyboard",
    "build_webapp_reply_keyboard",
]
