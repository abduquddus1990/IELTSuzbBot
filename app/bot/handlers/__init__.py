"""Telegram Bot Router Aggregation (`aiogram 3.x`)."""

from aiogram import Dispatcher, Router

from app.bot.handlers.billing_and_admin import router as billing_and_admin_router
from app.bot.handlers.exam_flow import router as exam_flow_router
from app.bot.handlers.start import router as start_router


def setup_bot_routers(dp: Dispatcher) -> Dispatcher:
    """Register all Telegram bot command, billing, admin, and FSM routers on the given `Dispatcher`."""
    dp.include_router(start_router)
    dp.include_router(billing_and_admin_router)
    dp.include_router(exam_flow_router)
    return dp


def build_root_router() -> Router:
    """Create a fresh root `Router` combining `start_router`, `billing_and_admin_router`, and `exam_flow_router`."""
    root = Router(name="root_bot_router")
    root.include_router(start_router)
    root.include_router(billing_and_admin_router)
    root.include_router(exam_flow_router)
    return root


__all__ = [
    "billing_and_admin_router",
    "build_root_router",
    "exam_flow_router",
    "setup_bot_routers",
    "start_router",
]
