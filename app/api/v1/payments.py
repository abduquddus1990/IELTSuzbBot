"""FastAPI Hybrid Payment & Admin Endpoints (`/api/v1/payments`).

Exposes:
1. `GET /api/v1/payments/config`: Active payment gateways (P2P Card, Telegram Stars XTR,
   dormant Click/Payme toggle) and tariff pricing catalog.
2. `POST /api/v1/payments/p2p-order`: Create a P2P Uzcard/Humo receipt verification order.
3. `POST /api/v1/payments/p2p-order/{order_id}/approve`: Admin 1-click approval (idempotent).
4. `POST /api/v1/payments/p2p-order/{order_id}/reject`: Admin rejection of invalid receipt.
5. `POST /api/v1/payments/click/prepare` & `/click/complete`: Dormant Click Shop API MD5 webhooks.
6. `POST /api/v1/payments/payme`: Dormant Payme Merchant JSON-RPC 2.0 webhook.
7. `GET /api/v1/payments/admin/stats`: Real-time platform user, credit, and revenue statistics.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.payment_service import (
    TARIFF_CATALOG,
    get_billing_ledger_service,
)

router = APIRouter(prefix="/payments", tags=["Payments & Admin"])


class P2POrderCreateRequest(BaseModel):
    """Request payload for creating a P2P card receipt order."""

    user_telegram_id: int = Field(..., description="Candidate Telegram user ID")
    full_name: str = Field(default="Candidate", description="Candidate full name")
    tariff_code: str = Field(default="full", description="Tariff code: full | writing | speaking")
    receipt_file_id: str | None = Field(
        default=None,
        description="Telegram file_id or URL of the uploaded payment receipt screenshot",
    )
    amount_uzs: int | None = Field(
        default=None,
        description="Optional override amount in UZS (defaults to tariff catalog price)",
    )
    credits: int = Field(default=1, ge=1, description="Number of exam credits to grant on approval")


class P2POrderApproveRequest(BaseModel):
    """Optional request body when an admin approves a P2P order."""

    admin_telegram_id: int = Field(default=0, description="Admin Telegram ID approving the order")


class P2POrderRejectRequest(BaseModel):
    """Optional request body when an admin rejects a P2P order."""

    admin_telegram_id: int = Field(default=0, description="Admin Telegram ID rejecting the order")
    reason: str = Field(default="Chek tasdiqlanmadi", description="Rejection reason in Uzbek")


class AdminCreditGrantRequest(BaseModel):
    """Request payload for granting bonus exam credits to a candidate."""

    user_telegram_id: int = Field(..., description="Candidate Telegram user ID")
    credits: int = Field(default=1, ge=1, description="Number of credits to grant")
    reason: str = Field(default="admin_grant", description="Audit reason for credit grant")


async def _parse_request_dict(request: Request) -> dict[str, Any]:
    """Extract dictionary payload from either JSON body or URL-encoded form data."""
    try:
        data = await request.json()
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    try:
        form = await request.form()
        return {k: v for k, v in form.items()}
    except Exception:
        return {}


@router.get("/config")
async def get_payments_config() -> dict[str, Any]:
    """Return active payment gateway settings and tariff catalog for Bot & WebApp."""
    return {
        "enable_p2p_card": settings.ENABLE_P2P_CARD,
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "card_holder": settings.PAYMENT_CARD_HOLDER,
        "card_bank": settings.PAYMENT_CARD_BANK,
        "enable_telegram_stars": settings.ENABLE_TELEGRAM_STARS,
        "enable_click_payme": settings.ENABLE_CLICK_PAYME,
        "free_trial_credits": settings.FREE_TRIAL_CREDITS,
        "tariffs": TARIFF_CATALOG,
    }


@router.post("/p2p-order")
async def create_p2p_order(payload: P2POrderCreateRequest) -> dict[str, Any]:
    """Create a pending P2P card transfer receipt order."""
    ledger = get_billing_ledger_service()
    order = ledger.create_p2p_receipt_order(
        user_telegram_id=payload.user_telegram_id,
        full_name=payload.full_name,
        tariff_code=payload.tariff_code,
        receipt_file_id=payload.receipt_file_id,
        amount_uzs=payload.amount_uzs,
        credits=payload.credits,
    )
    return order


@router.post("/p2p-order/{order_id}/approve")
async def approve_p2p_order(
    order_id: str,
    payload: P2POrderApproveRequest | None = Body(default=None),
) -> dict[str, Any]:
    """Approve a pending P2P card receipt order and grant exam credits idempotently."""
    ledger = get_billing_ledger_service()
    admin_id = payload.admin_telegram_id if payload is not None else 0
    try:
        return ledger.approve_p2p_order(order_id=order_id, admin_telegram_id=admin_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/p2p-order/{order_id}/reject")
async def reject_p2p_order(
    order_id: str,
    payload: P2POrderRejectRequest | None = Body(default=None),
) -> dict[str, Any]:
    """Reject a pending P2P card receipt order."""
    ledger = get_billing_ledger_service()
    admin_id = payload.admin_telegram_id if payload is not None else 0
    reason = payload.reason if payload is not None else "Chek tasdiqlanmadi"
    try:
        return ledger.reject_p2p_order(
            order_id=order_id,
            admin_telegram_id=admin_id,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/click/prepare")
async def click_prepare_webhook(request: Request) -> dict[str, Any]:
    """Handle Click Merchant API `Prepare` (`action=0`) webhook."""
    payload = await _parse_request_dict(request)
    payload.setdefault("action", 0)
    ledger = get_billing_ledger_service()
    return ledger.handle_click_webhook(payload)


@router.post("/click/complete")
async def click_complete_webhook(request: Request) -> dict[str, Any]:
    """Handle Click Merchant API `Complete` (`action=1`) webhook."""
    payload = await _parse_request_dict(request)
    payload.setdefault("action", 1)
    ledger = get_billing_ledger_service()
    return ledger.handle_click_webhook(payload)


@router.post("/payme")
async def payme_jsonrpc_webhook(request: Request) -> dict[str, Any]:
    """Handle Payme Merchant API JSON-RPC 2.0 webhook."""
    payload = await _parse_request_dict(request)
    auth_header = request.headers.get("Authorization")
    ledger = get_billing_ledger_service()
    return ledger.handle_payme_jsonrpc(payload=payload, auth_header=auth_header)


@router.get("/admin/stats")
async def get_admin_platform_stats() -> dict[str, Any]:
    """Return platform-wide user, credit, P2P order, Stars, and revenue statistics."""
    ledger = get_billing_ledger_service()
    return ledger.get_platform_stats()


@router.get("/credits/{user_telegram_id}")
async def get_user_credits_endpoint(user_telegram_id: int) -> dict[str, Any]:
    """Return a candidate's current exam credit balance."""
    ledger = get_billing_ledger_service()
    credits = ledger.get_user_credits(user_telegram_id)
    return {
        "user_telegram_id": user_telegram_id,
        "credits": credits,
    }


@router.post("/admin/grant")
async def admin_grant_credits(payload: AdminCreditGrantRequest) -> dict[str, Any]:
    """Grant bonus exam credits to a candidate account."""
    ledger = get_billing_ledger_service()
    new_balance = ledger.add_user_credits(
        user_telegram_id=payload.user_telegram_id,
        credits=payload.credits,
        reason=payload.reason,
    )
    return {
        "user_telegram_id": payload.user_telegram_id,
        "granted_credits": payload.credits,
        "new_credit_balance": new_balance,
    }


__all__ = ["router"]
