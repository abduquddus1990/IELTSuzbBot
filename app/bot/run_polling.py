"""Local Development Polling Entrypoint for the IELTS & CEFR Mock AI Telegram Bot.

Run via:
    python -m app.bot.run_polling
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path even if invoked outside the repository directory
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.bot import create_bot, create_dispatcher
from app.bot.handlers.exam_flow import is_placeholder_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialize directories, validate BOT_TOKEN, and start `aiogram 3.x` long polling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    reports_dir = Path(settings.PDF_OUTPUT_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)

    token = settings.BOT_TOKEN.strip()
    if is_placeholder_api_key(token) or ":" not in token:
        logger.error(
            "BOT_TOKEN is not configured yet! Please open `.env` and replace "
            "`BOT_TOKEN=PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE` with a real token from @BotFather."
        )
        sys.exit(1)

    if not is_placeholder_api_key(settings.ANTHROPIC_API_KEY):
        logger.info("AI Evaluator Mode: LIVE Anthropic Claude (%s)", settings.CLAUDE_WRITING_MODEL)
    elif not is_placeholder_api_key(settings.GEMINI_API_KEY):
        logger.info("AI Evaluator Mode: LIVE Google Gemini Multimodal (%s)", settings.GEMINI_MODEL)
    else:
        logger.warning(
            "GEMINI_API_KEY and ANTHROPIC_API_KEY are currently placeholders. Bot will run in "
            "Smart Demo Evaluation mode (generating real 2-page PDF Certificates at $0 API cost) "
            "until you insert GEMINI_API_KEY or ANTHROPIC_API_KEY in `.env`."
        )

    from aiogram.types import MenuButtonWebApp, WebAppInfo
    from app.bot.keyboards.exam_kb import _is_public_https_url, _resolve_webapp_url

    bot = create_bot(token=token)
    dp = create_dispatcher()

    logger.info("Starting %s Telegram Bot in Long-Polling mode...", settings.APP_NAME)
    try:
        info = await bot.get_webhook_info()
        if info.url and "--force" not in sys.argv:
            logger.error(
                "This bot is served by a webhook (%s), i.e. the production server. Local polling would "
                "disconnect it. Use a separate test bot token, or run with --force to take over.",
                info.url,
            )
            sys.exit(1)
        await bot.delete_webhook(drop_pending_updates=False)
        resolved_webapp = _resolve_webapp_url()
        if _is_public_https_url(resolved_webapp):
            try:
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text="📝 Mock Exam",
                        web_app=WebAppInfo(url=resolved_webapp),
                    )
                )
                logger.info("Telegram MenuButtonWebApp updated to: %s", resolved_webapp)
            except Exception as exc:
                logger.warning("Could not set MenuButtonWebApp: %s", exc)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Telegram Bot polling stopped.")
