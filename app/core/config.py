"""Application configuration powered by Pydantic v2 BaseSettings.

Loads environment variables from `.env` and provides strongly-typed configuration
for FastAPI, aiogram 3.x, SQLAlchemy 2.0 Async (Neon/Supabase), Anthropic Claude,
OpenAI Whisper, Cloudflare R2, and Click/Payme payment gateways.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Global application settings loaded from environment variables or `.env` file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- 1. Application & Server Settings ---
    APP_NAME: str = Field(default="IELTS & CEFR Mock AI")
    APP_ENV: Literal["development", "staging", "production"] = Field(default="development")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: str = Field(
        default="change-this-to-a-strong-random-64-char-hex-key-in-production"
    )
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    BASE_WEBHOOK_URL: str = Field(default="https://api.yourdomain.uz")
    WEBAPP_URL: str = Field(default="https://app.yourdomain.uz")

    # --- 2. Telegram Bot Settings (aiogram 3.x) ---
    BOT_TOKEN: str = Field(default="1234567890:AAH_your_telegram_bot_token_from_botfather")
    BOT_WEBHOOK_PATH: str = Field(default="/api/v1/webhook/telegram")
    BOT_WEBHOOK_SECRET: str = Field(default="telegram-webhook-secret-token-12345")
    ADMIN_TELEGRAM_IDS: str = Field(default="123456789,987654321")

    # --- 3. Database Settings (Supabase / Neon Serverless PostgreSQL) ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ielts_cefr_mock"
    )
    DB_ECHO: bool = Field(default=False)
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)

    # --- 4. AI Integrations (Google Gemini, Anthropic Claude & OpenAI Whisper) ---
    GEMINI_API_KEY: str = Field(default="PUT_YOUR_GEMINI_API_KEY_HERE")
    GEMINI_MODEL: str = Field(default="gemini-3.1-flash-lite")

    ANTHROPIC_API_KEY: str = Field(default="sk-ant-api03-placeholder")
    CLAUDE_WRITING_MODEL: str = Field(default="claude-3-5-sonnet-latest")
    CLAUDE_FAST_MODEL: str = Field(default="claude-3-5-haiku-latest")
    CLAUDE_VISION_MODEL: str = Field(default="claude-3-5-sonnet-latest")
    CLAUDE_MAX_TOKENS: int = Field(default=2500)
    CLAUDE_TEMPERATURE: float = Field(default=0.1)

    OPENAI_API_KEY: str = Field(default="sk-proj-placeholder")
    WHISPER_MODEL: str = Field(default="whisper-1")
    OPENAI_VISION_FALLBACK_MODEL: str = Field(default="gpt-4o-mini")
    OCR_PROVIDER: Literal["gemini", "claude", "openai"] = Field(default="gemini")

    # --- 5. Cloudflare R2 Storage (Zero-Egress S3 Compatible) ---
    R2_ACCOUNT_ID: str = Field(default="your_cloudflare_account_id")
    R2_ACCESS_KEY_ID: str = Field(default="your_r2_access_key_id")
    R2_SECRET_ACCESS_KEY: str = Field(default="your_r2_secret_access_key")
    R2_BUCKET_NAME: str = Field(default="ielts-cefr-mock-media")
    R2_ENDPOINT_URL: str = Field(
        default="https://your_cloudflare_account_id.r2.cloudflarestorage.com"
    )
    R2_PUBLIC_DOMAIN: str = Field(default="https://cdn.yourdomain.uz")

    # --- 6. Hybrid Payment Gateways (P2P Card + Telegram Stars + Switchable Click/Payme) ---
    ENABLE_P2P_CARD: bool = Field(default=True)
    PAYMENT_CARD_NUMBER: str = Field(default="8600 0000 0000 0000")
    PAYMENT_CARD_HOLDER: str = Field(default="IELTS MOCK AI ADMIN")
    PAYMENT_CARD_BANK: str = Field(default="Uzcard / Humo")

    ENABLE_TELEGRAM_STARS: bool = Field(default=True)
    PRICE_FULL_MOCK_STARS: int = Field(default=150)
    PRICE_WRITING_ONLY_STARS: int = Field(default=75)
    PRICE_SPEAKING_ONLY_STARS: int = Field(default=75)

    # Dormant Click & Payme Merchant API (set ENABLE_CLICK_PAYME=True when YaTT/MChJ is opened)
    ENABLE_CLICK_PAYME: bool = Field(default=False)
    CLICK_SERVICE_ID: str = Field(default="12345")
    CLICK_MERCHANT_ID: str = Field(default="12345")
    CLICK_SECRET_KEY: str = Field(default="your_click_secret_key")
    CLICK_MERCHANT_USER_ID: str = Field(default="12345")

    PAYME_MERCHANT_ID: str = Field(default="your_payme_merchant_id")
    PAYME_SECRET_KEY: str = Field(default="your_payme_production_key")
    PAYME_TEST_KEY: str = Field(default="your_payme_sandbox_test_key")
    PAYME_IS_TEST: bool = Field(default=True)

    # --- 7. Business & Tariff Pricing (UZS) ---
    PRICE_FULL_MOCK_UZS: int = Field(default=40000)
    PRICE_WRITING_ONLY_UZS: int = Field(default=15000)
    PRICE_SPEAKING_ONLY_UZS: int = Field(default=15000)
    FREE_TRIAL_CREDITS: int = Field(default=1)

    # --- 8. PDF Report Settings ---
    PDF_OUTPUT_DIR: str = Field(default="storage/reports")
    PDF_DISCLAIMER_TEXT: str = Field(
        default=(
            "Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool). "
            "Ushbu hujjat rasmiy Cambridge, IDP, British Council yoki Bilim va malakalarni "
            "baholash agentligi (BBA) sertifikati hisoblanmaydi."
        )
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_ids_list(self) -> list[int]:
        """Parse comma-separated ADMIN_TELEGRAM_IDS into a list of integers."""
        if not self.ADMIN_TELEGRAM_IDS.strip():
            return []
        return [
            int(item.strip())
            for item in self.ADMIN_TELEGRAM_IDS.split(",")
            if item.strip().isdigit()
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_webhook_url(self) -> str:
        """Construct the full Telegram webhook URL."""
        return f"{self.BASE_WEBHOOK_URL.rstrip('/')}/{self.BOT_WEBHOOK_PATH.lstrip('/')}"


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application Settings."""
    return Settings()


settings = get_settings()
