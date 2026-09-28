"""FastAPI + aiogram 3.x Webhook & Mini App Application Entrypoint for IELTS & CEFR Mock AI."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, status
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
import os

bot_dispatcher = create_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown lifecycle resources (database pool, report directories, optional cloud bot polling)."""
    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    if not reports_dir.is_absolute():
        reports_dir = BASE_DIR / reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    polling_task: asyncio.Task[Any] | None = None
    polling_bot = None
    if os.environ.get("RUN_BOT_POLLING_IN_WEB", "").strip().lower() in {"1", "true", "yes"}:
        token = settings.BOT_TOKEN.strip()
        if not is_placeholder_api_key(token) and ":" in token:
            from aiogram.types import MenuButtonWebApp, WebAppInfo
            from app.bot.keyboards.exam_kb import _is_public_https_url, _resolve_webapp_url

            polling_bot = create_bot(token=token)
            await polling_bot.delete_webhook(drop_pending_updates=True)
            resolved_webapp = _resolve_webapp_url()
            if _is_public_https_url(resolved_webapp):
                try:
                    await polling_bot.set_chat_menu_button(
                        menu_button=MenuButtonWebApp(
                            text="📱 Imtihon (App)",
                            web_app=WebAppInfo(url=resolved_webapp),
                        )
                    )
                except Exception:
                    pass
            polling_task = asyncio.create_task(
                bot_dispatcher.start_polling(polling_bot, handle_signals=False)
            )

    yield

    if polling_task is not None:
        polling_task.cancel()
    if polling_bot is not None:
        await polling_bot.session.close()
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
        update: dict[str, Any],
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> dict[str, bool]:
        """Receive incoming Telegram updates via webhook, verify secret token, and feed to aiogram."""
        if (
            settings.APP_ENV == "production"
            and x_telegram_bot_api_secret_token != settings.BOT_WEBHOOK_SECRET
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram webhook secret token.",
            )

        if not is_placeholder_api_key(settings.BOT_TOKEN) and ":" in settings.BOT_TOKEN:
            bot = create_bot()
            try:
                telegram_update = Update.model_validate(update, context={"bot": bot})
                await bot_dispatcher.feed_update(bot=bot, update=telegram_update)
            finally:
                await bot.session.close()

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
