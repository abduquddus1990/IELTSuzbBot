"""Telegram Bot Router Aggregation (`aiogram 3.x`).

The platform is free, so the dormant payment/billing router (`billing_and_admin.py`) is not
registered. Re-enable it here if paid plans are ever introduced.
"""

from aiogram import Dispatcher, Router

from app.bot.handlers.exam_flow import router as exam_flow_router
from app.bot.handlers.start import router as start_router


def setup_bot_routers(dp: Dispatcher) -> Dispatcher:
    """Register command and practice-flow routers on the given `Dispatcher`."""
    dp.include_router(start_router)
    dp.include_router(exam_flow_router)
    return dp


def build_root_router() -> Router:
    root = Router(name="root_bot_router")
    root.include_router(start_router)
    root.include_router(exam_flow_router)
    return root


__all__ = [
    "build_root_router",
    "exam_flow_router",
    "setup_bot_routers",
    "start_router",
]
