"""Telegram bot package powered by `aiogram 3.x` for IELTS & CEFR Mock AI."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import exam_flow_router, setup_bot_routers, start_router
from app.bot.keyboards import (
    build_exam_mode_keyboard,
    build_exam_type_keyboard,
    build_listening_reading_keyboard,
    build_main_menu_keyboard,
)
from app.bot.states import ExamSessionStates
from app.core.config import settings


def create_bot(token: str | None = None) -> Bot:
    """Instantiate an `aiogram.Bot` with HTML default parse mode."""
    resolved_token = (token or settings.BOT_TOKEN).strip()
    return Bot(
        token=resolved_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Create an `aiogram.Dispatcher` with `MemoryStorage` and all exam FSM routers attached."""
    dp = Dispatcher(storage=MemoryStorage())
    setup_bot_routers(dp)
    return dp


__all__ = [
    "ExamSessionStates",
    "build_exam_mode_keyboard",
    "build_exam_type_keyboard",
    "build_listening_reading_keyboard",
    "build_main_menu_keyboard",
    "create_bot",
    "create_dispatcher",
    "exam_flow_router",
    "setup_bot_routers",
    "start_router",
]
