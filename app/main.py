"""FastAPI + aiogram 3.x Webhook & Mini App Application Entrypoint for IELTS & CEFR Mock AI."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.bot import create_bot, create_dispatcher
from app.bot.handlers.exam_flow import is_placeholder_api_key
from app.core.config import BASE_DIR, settings

try:
    from app.db.session import engine
except ImportError:  # pragma: no cover
    engine = None  # type: ignore[assignment]

import asyncio
import hashlib
import hmac
import logging
import os
import re

bot_dispatcher = create_dispatcher()
logger = logging.getLogger(__name__)
_background_updates: set[asyncio.Task[Any]] = set()


def _bot_token_ok() -> bool:
    token = settings.BOT_TOKEN.strip()
    return not is_placeholder_api_key(token) and ":" in token


def bot_mode() -> str:
    """How Telegram updates reach the bot: 'webhook', 'polling' or 'off'.

    On Render a webhook is used automatically: Telegram's HTTPS call wakes the sleeping free
    instance, whereas a polling loop dies with it. Override with BOT_MODE.
    """
    explicit = os.environ.get("BOT_MODE", "").strip().lower()
    if explicit in {"webhook", "polling", "off"}:
        return explicit
    if os.environ.get("RENDER_EXTERNAL_URL", "").strip():
        return "webhook"
    if os.environ.get("RUN_BOT_POLLING_IN_WEB", "").strip().lower() in {"1", "true", "yes"}:
        return "polling"
    return "off"


def webhook_secret() -> str:
    """Secret Telegram echoes in X-Telegram-Bot-Api-Secret-Token (derived from SECRET_KEY by default)."""
    configured = settings.BOT_WEBHOOK_SECRET.strip()
    if configured and configured != "telegram-webhook-secret-token-12345" and re.fullmatch(r"[A-Za-z0-9_-]{1,256}", configured):
        return configured
    return hmac.new(settings.SECRET_KEY.encode(), b"telegram-webhook", hashlib.sha256).hexdigest()


def webhook_url() -> str:
    base = os.environ.get("RENDER_EXTERNAL_URL", "").strip() or settings.BASE_WEBHOOK_URL
    return f"{base.rstrip('/')}/{settings.BOT_WEBHOOK_PATH.lstrip('/')}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Prepare storage dirs and connect the Telegram bot (webhook on Render, polling locally)."""
    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    if not reports_dir.is_absolute():
        reports_dir = BASE_DIR / reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    if settings.APP_ENV == "production" and settings.SECRET_KEY.startswith("change-this"):
        logger.error("SECRET_KEY is the default value: PDF report links can be forged. Set SECRET_KEY in the environment.")

    mode = bot_mode() if _bot_token_ok() else "off"
    app.state.bot = None
    polling_task: asyncio.Task[Any] | None = None
    if mode != "off":
        from aiogram.types import MenuButtonWebApp, WebAppInfo

        from app.bot.keyboards.exam_kb import _is_public_https_url, _resolve_webapp_url

        bot = create_bot()
        app.state.bot = bot
        resolved_webapp = _resolve_webapp_url()
        try:
            if _is_public_https_url(resolved_webapp):
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="📝 Mock Exam", web_app=WebAppInfo(url=resolved_webapp))
                )
            if mode == "webhook":
                await bot.set_webhook(
                    url=webhook_url(),
                    secret_token=webhook_secret(),
                    allowed_updates=bot_dispatcher.resolve_used_update_types(),
                    drop_pending_updates=False,  # keep messages sent while the server was asleep
                )
                logger.info("Telegram webhook set to %s", webhook_url())
            else:
                await bot.delete_webhook(drop_pending_updates=False)
                polling_task = asyncio.create_task(bot_dispatcher.start_polling(bot, handle_signals=False))
                logger.info("Telegram bot polling started")
        except Exception as exc:  # never block the web app because Telegram is unreachable
            logger.error("Telegram bot setup failed (%s mode): %s", mode, exc)

    yield

    if polling_task is not None:
        polling_task.cancel()
    if app.state.bot is not None:
        await app.state.bot.session.close()
    if engine is not None:
        await engine.dispose()


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application with v1 routes and `/webapp` static files."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description=(
            "IELTS (0.0-9.0 Band) & Uzbekistan National CEFR (B1-C1, 0-75 Scale) "
            "Mock AI Assessment Platform — Unofficial Mock Assessment Tool."
        ),
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    allowed_origins = (
        ["*"]
        if settings.DEBUG
        else [settings.WEBAPP_URL, "http://localhost:3000", "http://localhost:5173"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount REST API v1 routes (/api/v1/...)
    app.include_router(api_v1_router)

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        """Browser visitors landing on the bare domain go straight to the exam app."""
        return RedirectResponse(url="/webapp/")

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        """Root liveness and readiness probe endpoint."""
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }

    @app.post(settings.BOT_WEBHOOK_PATH, tags=["Telegram Webhook"])
    async def telegram_webhook(
        request: Request,
        update: dict[str, Any],
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> dict[str, bool]:
        """Receive a Telegram update, verify the secret, and process it in the background.

        Answering immediately stops Telegram from re-sending the same update while a slow AI
        evaluation is running.
        """
        if not hmac.compare_digest(x_telegram_bot_api_secret_token or "", webhook_secret()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret token.")
        bot = getattr(request.app.state, "bot", None)
        if bot is None:
            return {"ok": True}
        telegram_update = Update.model_validate(update, context={"bot": bot})
        task = asyncio.create_task(bot_dispatcher.feed_update(bot=bot, update=telegram_update))
        _background_updates.add(task)

        def _done(t: asyncio.Task[Any]) -> None:
            _background_updates.discard(t)
            if not t.cancelled() and t.exception() is not None:
                logger.error("Telegram update %s failed: %r", telegram_update.update_id, t.exception())

        task.add_done_callback(_done)
        return {"ok": True}

    # Mount Telegram Mini App (WebApp) static files at /webapp if directory exists
    webapp_dir = BASE_DIR / "webapp"
    if webapp_dir.exists() and webapp_dir.is_dir():
        app.mount(
            "/webapp",
            StaticFiles(directory=str(webapp_dir), html=True),
            name="webapp",
        )

    return app


app = create_app()
