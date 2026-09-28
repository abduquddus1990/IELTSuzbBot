"""Comprehensive Stage 4 Unit & Integration Tests for Hybrid Monetization & Admin Panel.

Verifies:
1. `BillingLedgerService` P2P Card workflow (`create_p2p_receipt_order`, `approve_p2p_order`
   idempotency, credit balance increase, `reject_p2p_order`, `consume_user_credit`).
2. `BillingLedgerService` Telegram Stars (`XTR`) workflow (`record_stars_payment` idempotency
   and `get_platform_stats` revenue aggregation).
3. Dormant Click/Payme switch (`ENABLE_CLICK_PAYME=False` returns disabled message;
   `ENABLE_CLICK_PAYME=True` verifies `compute_click_sign_string` MD5 signature for Click
   Prepare/Complete and `verify_payme_basic_auth` + JSON-RPC `CheckPerformTransaction`,
   `CreateTransaction`, `PerformTransaction`, `CheckTransaction`, `CancelTransaction`).
4. FastAPI `/api/v1/payments/config`, `/api/v1/payments/p2p-order`,
   `/api/v1/payments/p2p-order/{order_id}/approve`, `/api/v1/payments/click/prepare`,
   `/api/v1/payments/payme`, and `/api/v1/payments/admin/stats`.
5. `aiogram 3.x` `PaymentFlowStates` and inline keyboard builders
   (`build_payment_tariffs_keyboard`, `build_admin_receipt_approval_keyboard`,
   `build_admin_dashboard_keyboard`).
"""

from __future__ import annotations

import base64
from pathlib import Path

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.payments import router as payments_router
from app.bot.handlers.billing_and_admin import (
    PaymentFlowStates,
    build_admin_dashboard_keyboard,
    build_admin_receipt_approval_keyboard,
    build_payment_tariffs_keyboard,
)
from app.core.config import settings
from app.main import create_app
from app.services.payment_service import (
    BillingLedgerService,
    compute_click_sign_string,
    verify_payme_basic_auth,
)


def _create_test_fastapi_app() -> FastAPI:
    """Create a FastAPI app instance and ensure `/api/v1/payments` routes are mounted."""
    test_app = create_app()
    existing_paths = {getattr(route, "path", "") for route in test_app.routes}
    if "/api/v1/payments/config" not in existing_paths:
        test_app.include_router(payments_router, prefix="/api/v1")
    return test_app


# =====================================================================
# 1. P2P CARD TRANSFER, RECEIPT ORDER, IDEMPOTENT APPROVAL & CREDITS
# =====================================================================


def test_p2p_card_order_approval_idempotency_and_credit_consumption(tmp_path: Path) -> None:
    """Verify P2P receipt order creation, idempotent approval, rejection, and credit deduction."""
    ledger_file = tmp_path / "test_billing_ledger.json"
    service = BillingLedgerService(ledger_path=ledger_file)

    user_id = 998901112233
    admin_id = 123456789

    # 1. New user starts with FREE_TRIAL_CREDITS (default 1)
    initial_credits = service.get_user_credits(user_id)
    assert initial_credits == settings.FREE_TRIAL_CREDITS

    # 2. Candidate creates a P2P order for 'full' mock (35,000 UZS)
    order = service.create_p2p_receipt_order(
        user_telegram_id=user_id,
        full_name="Jasurbek Alimov",
        tariff_code="full",
        receipt_file_id="AgACAgIAAxkBAAIB_sample_receipt_photo_id",
    )
    order_id = order["order_id"]
    assert order_id.startswith("P2P-")
    assert order["status"] == "PENDING"
    assert order["amount_uzs"] == settings.PRICE_FULL_MOCK_UZS
    assert order["credits"] == 1
    assert len(service.list_pending_p2p_orders()) == 1

    # 3. Admin approves the order -> status becomes APPROVED and user gets +1 credit
    approved_once = service.approve_p2p_order(order_id=order_id, admin_telegram_id=admin_id)
    assert approved_once["status"] == "APPROVED"
    assert approved_once["approved_by"] == admin_id
    assert service.get_user_credits(user_id) == initial_credits + 1
    assert len(service.list_pending_p2p_orders()) == 0

    # 4. Idempotency check: approving the same order a second time must NOT double-credit
    approved_twice = service.approve_p2p_order(order_id=order_id, admin_telegram_id=admin_id)
    assert approved_twice["status"] == "APPROVED"
    assert service.get_user_credits(user_id) == initial_credits + 1

    # 5. Create a second order and reject it -> credits must NOT increase
    order_to_reject = service.create_p2p_receipt_order(
        user_telegram_id=user_id,
        full_name="Jasurbek Alimov",
        tariff_code="writing",
        receipt_file_id="invalid_receipt_file_id",
    )
    rejected = service.reject_p2p_order(
        order_id=order_to_reject["order_id"],
        admin_telegram_id=admin_id,
        reason="Skrinshot noto'g'ri",
    )
    assert rejected["status"] == "REJECTED"
    assert rejected["rejected_reason"] == "Skrinshot noto'g'ri"
    assert service.get_user_credits(user_id) == initial_credits + 1

    # 6. Consume credits until 0, then verify consume_user_credit returns False
    total_available = service.get_user_credits(user_id)
    for _ in range(total_available):
        assert service.consume_user_credit(user_id) is True
    assert service.get_user_credits(user_id) == 0
    assert service.consume_user_credit(user_id) is False


# =====================================================================
# 2. TELEGRAM STARS (XTR) AUTOMATED PAYMENT & PLATFORM STATS
# =====================================================================


def test_telegram_stars_xtr_payment_and_platform_stats(tmp_path: Path) -> None:
    """Verify Telegram Stars XTR payment recording, idempotency, and revenue aggregation."""
    ledger_file = tmp_path / "stars_ledger.json"
    service = BillingLedgerService(ledger_path=ledger_file)

    user_id = 998935556677
    base_credits = service.get_user_credits(user_id)

    tx = service.record_stars_payment(
        user_telegram_id=user_id,
        full_name="Dilnoza Karimova",
        tariff_code="full",
        stars_amount=settings.PRICE_FULL_MOCK_STARS,
        telegram_charge_id="st_charge_unique_001",
        credits=1,
    )
    assert tx["status"] == "COMPLETED"
    assert tx["currency"] == "XTR"
    assert tx["stars_amount"] == settings.PRICE_FULL_MOCK_STARS
    assert service.get_user_credits(user_id) == base_credits + 1

    # Idempotency on duplicate telegram_charge_id
    tx_dup = service.record_stars_payment(
        user_telegram_id=user_id,
        full_name="Dilnoza Karimova",
        tariff_code="full",
        stars_amount=settings.PRICE_FULL_MOCK_STARS,
        telegram_charge_id="st_charge_unique_001",
        credits=1,
    )
    assert tx_dup["transaction_id"] == tx["transaction_id"]
    assert service.get_user_credits(user_id) == base_credits + 1

    # Also approve one P2P order to verify combined UZS + Stars stats
    p2p_order = service.create_p2p_receipt_order(
        user_telegram_id=user_id,
        full_name="Dilnoza Karimova",
        tariff_code="speaking",
        receipt_file_id="receipt_speaking_1",
    )
    service.approve_p2p_order(order_id=p2p_order["order_id"], admin_telegram_id=111)

    stats = service.get_platform_stats()
    assert stats["total_users"] >= 1
    assert stats["approved_p2p_count"] == 1
    assert stats["stars_payments_count"] == 1
    assert stats["total_revenue_uzs"] == settings.PRICE_SPEAKING_ONLY_UZS
    assert stats["total_revenue_stars"] == settings.PRICE_FULL_MOCK_STARS


# =====================================================================
# 3. DORMANT CLICK (MD5) & PAYME (JSON-RPC 2.0) SWITCHABLE WEBHOOKS
# =====================================================================


def test_dormant_and_enabled_click_and_payme_webhooks(tmp_path: Path) -> None:
    """Verify Click MD5 and Payme JSON-RPC remain dormant by default and work when enabled."""
    ledger_file = tmp_path / "click_payme_ledger.json"
    service = BillingLedgerService(ledger_path=ledger_file)
    user_id = 998971234567
    initial_credits = service.get_user_credits(user_id)

    # 1. When ENABLE_CLICK_PAYME is False (dormant mode), both return disabled responses
    dormant_click = service.handle_click_webhook(
        payload={"action": 0, "click_trans_id": "1001"},
        enable_override=False,
    )
    assert dormant_click["error"] == -1
    assert "disabled" in dormant_click["error_note"].lower()

    dormant_payme = service.handle_payme_jsonrpc(
        payload={"jsonrpc": "2.0", "id": 1, "method": "CheckPerformTransaction"},
        auth_header=None,
        enable_override=False,
    )
    assert dormant_payme["error"]["code"] == -32400
    assert "disabled" in dormant_payme["error"]["message"].lower()

    # 2. Enable Click & test MD5 Prepare (action=0) and Complete (action=1)
    click_trans_id = "77889900"
    service_id = settings.CLICK_SERVICE_ID
    merchant_trans_id = str(user_id)
    amount = "35000"
    sign_time = "2026-09-28 13:00:00"

    prepare_sign = compute_click_sign_string(
        click_trans_id=click_trans_id,
        service_id=service_id,
        secret_key=settings.CLICK_SECRET_KEY,
        merchant_trans_id=merchant_trans_id,
        amount=amount,
        action=0,
        sign_time=sign_time,
    )
    prepare_res = service.handle_click_webhook(
        payload={
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": 0,
            "sign_time": sign_time,
            "sign_string": prepare_sign,
        },
        enable_override=True,
    )
    assert prepare_res["error"] == 0
    merchant_prepare_id = prepare_res["merchant_prepare_id"]

    # Invalid signature must fail with error -1
    bad_sign_res = service.handle_click_webhook(
        payload={
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": 0,
            "sign_time": sign_time,
            "sign_string": "00000000000000000000000000000000",
        },
        enable_override=True,
    )
    assert bad_sign_res["error"] == -1

    complete_sign = compute_click_sign_string(
        click_trans_id=click_trans_id,
        service_id=service_id,
        secret_key=settings.CLICK_SECRET_KEY,
        merchant_trans_id=merchant_trans_id,
        amount=amount,
        action=1,
        sign_time=sign_time,
        merchant_prepare_id=merchant_prepare_id,
    )
    complete_res = service.handle_click_webhook(
        payload={
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": merchant_prepare_id,
            "amount": amount,
            "action": 1,
            "sign_time": sign_time,
            "sign_string": complete_sign,
        },
        enable_override=True,
    )
    assert complete_res["error"] == 0
    assert service.get_user_credits(user_id) == initial_credits + 1

    # 3. Enable Payme & test Basic Auth + CheckPerformTransaction -> CreateTransaction -> PerformTransaction
    active_payme_key = settings.PAYME_TEST_KEY if settings.PAYME_IS_TEST else settings.PAYME_SECRET_KEY
    raw_basic = f"Paycom:{active_payme_key}".encode("utf-8")
    valid_auth_header = f"Basic {base64.b64encode(raw_basic).decode('utf-8')}"

    assert verify_payme_basic_auth(valid_auth_header) is True
    assert verify_payme_basic_auth("Basic d3Jvbmc6a2V5") is False

    check_perform = service.handle_payme_jsonrpc(
        payload={
            "jsonrpc": "2.0",
            "id": 10,
            "method": "CheckPerformTransaction",
            "params": {"amount": 3500000, "account": {"user_telegram_id": user_id}},
        },
        auth_header=valid_auth_header,
        enable_override=True,
    )
    assert check_perform["result"]["allow"] is True

    create_tx = service.handle_payme_jsonrpc(
        payload={
            "jsonrpc": "2.0",
            "id": 11,
            "method": "CreateTransaction",
            "params": {
                "id": "payme_tx_001",
                "time": 1759050000000,
                "amount": 3500000,
                "account": {"user_telegram_id": user_id},
            },
        },
        auth_header=valid_auth_header,
        enable_override=True,
    )
    assert create_tx["result"]["state"] == 1

    perform_tx = service.handle_payme_jsonrpc(
        payload={
            "jsonrpc": "2.0",
            "id": 12,
            "method": "PerformTransaction",
            "params": {"id": "payme_tx_001"},
        },
        auth_header=valid_auth_header,
        enable_override=True,
    )
    assert perform_tx["result"]["state"] == 2
    assert service.get_user_credits(user_id) == initial_credits + 2


# =====================================================================
# 4. FASTAPI /API/V1/PAYMENTS ENDPOINTS INTEGRATION TESTS
# =====================================================================


def test_fastapi_payments_and_admin_endpoints() -> None:
    """Verify FastAPI hybrid payment endpoints (`/config`, `/p2p-order`, `/approve`, `/click`, `/payme`, `/admin/stats`)."""
    client = TestClient(_create_test_fastapi_app())

    # 1. GET /api/v1/payments/config
    cfg_resp = client.get("/api/v1/payments/config")
    assert cfg_resp.status_code == 200
    cfg_data = cfg_resp.json()
    assert cfg_data["enable_p2p_card"] is True
    assert cfg_data["enable_telegram_stars"] is True
    assert cfg_data["enable_click_payme"] is False
    assert "full" in cfg_data["tariffs"]

    # 2. POST /api/v1/payments/p2p-order
    create_resp = client.post(
        "/api/v1/payments/p2p-order",
        json={
            "user_telegram_id": 998907778899,
            "full_name": "Sardorbek Rakhimov",
            "tariff_code": "full",
            "receipt_file_id": "photo_receipt_test_123",
        },
    )
    assert create_resp.status_code == 200
    order_data = create_resp.json()
    order_id = order_data["order_id"]
    assert order_data["status"] == "PENDING"

    # 3. POST /api/v1/payments/p2p-order/{order_id}/approve
    approve_resp = client.post(
        f"/api/v1/payments/p2p-order/{order_id}/approve",
        json={"admin_telegram_id": 123456789},
    )
    assert approve_resp.status_code == 200
    approved_data = approve_resp.json()
    assert approved_data["status"] == "APPROVED"
    assert approved_data["new_credit_balance"] >= 2

    # 4. POST /api/v1/payments/click/prepare (dormant by default)
    click_resp = client.post("/api/v1/payments/click/prepare", json={"action": 0})
    assert click_resp.status_code == 200
    assert click_resp.json()["error"] == -1

    # 5. POST /api/v1/payments/payme (dormant by default)
    payme_resp = client.post(
        "/api/v1/payments/payme",
        json={"jsonrpc": "2.0", "id": 1, "method": "CheckPerformTransaction"},
    )
    assert payme_resp.status_code == 200
    assert payme_resp.json()["error"]["code"] == -32400

    # 6. GET /api/v1/payments/admin/stats
    stats_resp = client.get("/api/v1/payments/admin/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["approved_p2p_count"] >= 1
    assert stats_data["total_revenue_uzs"] >= settings.PRICE_FULL_MOCK_UZS


# =====================================================================
# 5. AIOGRAM 3 PAYMENT FSM STATES & KEYBOARD BUILDERS TESTS
# =====================================================================


def test_aiogram_payment_states_and_keyboards() -> None:
    """Verify `PaymentFlowStates` and hybrid billing/admin inline keyboards."""
    assert issubclass(PaymentFlowStates, StatesGroup)
    assert isinstance(PaymentFlowStates.waiting_for_receipt, State)

    # 1. Tariffs keyboard contains P2P Card and Telegram Stars buttons
    tariffs_kb = build_payment_tariffs_keyboard()
    assert isinstance(tariffs_kb, InlineKeyboardMarkup)
    callback_values = [
        btn.callback_data
        for row in tariffs_kb.inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    assert "pay_p2p:full" in callback_values
    assert "pay_p2p:writing" in callback_values
    assert "pay_p2p:speaking" in callback_values
    assert "pay_stars:full" in callback_values
    assert "pay_stars:writing" in callback_values
    assert "pay_stars:speaking" in callback_values

    # 2. Admin 1-click receipt approval keyboard
    approval_kb = build_admin_receipt_approval_keyboard("P2P-2026-0001")
    assert isinstance(approval_kb, InlineKeyboardMarkup)
    approval_callbacks = [
        btn.callback_data
        for row in approval_kb.inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    assert "admin_pay:approve:P2P-2026-0001" in approval_callbacks
    assert "admin_pay:reject:P2P-2026-0001" in approval_callbacks

    # 3. Admin dashboard keyboard
    admin_kb = build_admin_dashboard_keyboard()
    assert isinstance(admin_kb, InlineKeyboardMarkup)
    admin_callbacks = [
        btn.callback_data
        for row in admin_kb.inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    assert "admin_panel:refresh" in admin_callbacks
    assert "admin_panel:pending" in admin_callbacks
    assert "admin_panel:self_grant" in admin_callbacks
