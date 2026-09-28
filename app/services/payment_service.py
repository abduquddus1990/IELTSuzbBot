"""Hybrid Billing & Payment Ledger Service for IELTS & CEFR Mock AI.

Implements the 3-tier monetization architecture for Uzbekistan EdTech:
1. Tier 1 (Active by default): P2P Uzcard/Humo Card Transfer + Receipt Screenshot Verification
   with 1-click Admin Approval (`ENABLE_P2P_CARD=True`).
2. Tier 2 (Active by default): Telegram Stars (`XTR`) native automated in-app payments
   requiring zero legal entity (`ENABLE_TELEGRAM_STARS=True`).
3. Tier 3 (Dormant / Switchable): Click Merchant (Prepare/Complete MD5 webhook) and
   Payme Merchant (JSON-RPC 2.0 Basic Auth webhook), dormant while `ENABLE_CLICK_PAYME=False`
   and ready for instant activation when a legal entity (YaTT/MChJ) is registered.

Persists state to `storage/billing_ledger.json` alongside an in-memory dictionary so the
entire platform runs out-of-the-box with zero external database setup required.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

# Official Tariff Catalog (UZS + Telegram Stars XTR + Exam Credits)
TARIFF_CATALOG: dict[str, dict[str, Any]] = {
    "full": {
        "code": "full",
        "title_uz": "🏆 To'liq 4-Skill Mock (L+R+W+S + PDF)",
        "amount_uzs": settings.PRICE_FULL_MOCK_UZS,
        "stars": settings.PRICE_FULL_MOCK_STARS,
        "credits": 1,
    },
    "writing": {
        "code": "writing",
        "title_uz": "✍️ Faqat Writing (Task 1 + Task 2 + OCR + PDF)",
        "amount_uzs": settings.PRICE_WRITING_ONLY_UZS,
        "stars": settings.PRICE_WRITING_ONLY_STARS,
        "credits": 1,
    },
    "speaking": {
        "code": "speaking",
        "title_uz": "🎙 Faqat Speaking (Part 1-3 + Whisper + PDF)",
        "amount_uzs": settings.PRICE_SPEAKING_ONLY_UZS,
        "stars": settings.PRICE_SPEAKING_ONLY_STARS,
        "credits": 1,
    },
}


def compute_click_sign_string(
    click_trans_id: str | int,
    service_id: str | int,
    secret_key: str,
    merchant_trans_id: str,
    amount: str | float,
    action: int | str,
    sign_time: str,
    merchant_prepare_id: str | int | None = None,
) -> str:
    """Compute the official Click Shop API MD5 signature (`sign_string`).

    - Prepare (`action == 0`):
      `md5(f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}")`
    - Complete (`action == 1`):
      `md5(f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}")`
    """
    action_int = int(action)
    if action_int == 1 and merchant_prepare_id is not None and str(merchant_prepare_id) != "":
        raw = (
            f"{click_trans_id}{service_id}{secret_key}"
            f"{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
        )
    else:
        raw = (
            f"{click_trans_id}{service_id}{secret_key}"
            f"{merchant_trans_id}{amount}{action}{sign_time}"
        )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def verify_payme_basic_auth(
    auth_header: str | None,
    secret_key: str | None = None,
) -> bool:
    """Verify Payme Merchant HTTP Basic Authentication header (`Paycom:<KEY>`).

    Args:
        auth_header: Raw `Authorization` header (e.g., `"Basic UGF5Y29tOnNlY3JldA=="`).
        secret_key: Optional explicit key override. If omitted, checks configured
            Payme test/production keys from `settings`.
    """
    if not auth_header or not auth_header.startswith("Basic "):
        return False

    encoded_part = auth_header[len("Basic ") :].strip()
    if not encoded_part:
        return False

    try:
        decoded = base64.b64decode(encoded_part).decode("utf-8")
    except Exception:
        return False

    login, sep, password = decoded.partition(":")
    if not sep or login != "Paycom":
        return False

    if secret_key is not None:
        return hmac.compare_digest(password, secret_key)

    valid_keys = {
        settings.PAYME_TEST_KEY if settings.PAYME_IS_TEST else settings.PAYME_SECRET_KEY,
        settings.PAYME_SECRET_KEY,
        settings.PAYME_TEST_KEY,
    }
    non_empty_keys = {k for k in valid_keys if k}
    if not non_empty_keys:
        return hmac.compare_digest(password, "")
    return any(hmac.compare_digest(password, candidate) for candidate in non_empty_keys)


class BillingLedgerService:
    """Hybrid billing ledger managing user exam credits, P2P receipts, Stars, and Click/Payme."""

    def __init__(self, ledger_path: Path | str | None = None) -> None:
        self.ledger_path: Path = (
            Path(ledger_path)
            if ledger_path is not None
            else (BASE_DIR / "storage" / "billing_ledger.json")
        )
        self._state: dict[str, Any] = {
            "users": {},
            "orders": {},
            "stars_transactions": {},
            "click_transactions": {},
            "payme_transactions": {},
            "credit_history": [],
        }
        self._load_state()

    # Attach static helpers so callers can invoke them on either the module or service instance
    compute_click_sign_string = staticmethod(compute_click_sign_string)
    verify_payme_basic_auth = staticmethod(verify_payme_basic_auth)

    def _load_state(self) -> None:
        """Load persisted billing state from disk if available."""
        try:
            if self.ledger_path.exists():
                raw = self.ledger_path.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    for key in self._state:
                        if key in loaded and isinstance(loaded[key], type(self._state[key])):
                            self._state[key] = loaded[key]
        except Exception as exc:
            logger.warning("Could not load billing ledger from %s: %s", self.ledger_path, exc)

    def _save_state(self) -> None:
        """Persist in-memory billing state to `storage/billing_ledger.json`."""
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            self.ledger_path.write_text(
                json.dumps(self._state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Could not save billing ledger to %s: %s", self.ledger_path, exc)

    def _ensure_user_record(
        self,
        user_telegram_id: int,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """Return user record, auto-initializing new users with `FREE_TRIAL_CREDITS`."""
        user_key = str(user_telegram_id)
        users = self._state["users"]
        if user_key not in users:
            users[user_key] = {
                "user_telegram_id": int(user_telegram_id),
                "full_name": full_name or f"Candidate {user_telegram_id}",
                "credits": int(settings.FREE_TRIAL_CREDITS),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_state()
        elif full_name and users[user_key].get("full_name") != full_name:
            users[user_key]["full_name"] = full_name
            users[user_key]["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_state()
        return users[user_key]

    # -------------------------------------------------------------------------
    # 1. User Exam Credits Management
    # -------------------------------------------------------------------------

    def get_user_credits(self, user_telegram_id: int) -> int:
        """Return candidate's current exam credit balance (auto-initializes free trial)."""
        record = self._ensure_user_record(user_telegram_id)
        return int(record.get("credits", 0))

    def add_user_credits(
        self,
        user_telegram_id: int,
        credits: int,
        reason: str = "admin_grant",
    ) -> int:
        """Add exam credits to a user account and return the updated credit balance."""
        record = self._ensure_user_record(user_telegram_id)
        added = int(credits)
        record["credits"] = int(record.get("credits", 0)) + added
        record["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._state["credit_history"].append(
            {
                "user_telegram_id": int(user_telegram_id),
                "delta": added,
                "new_balance": record["credits"],
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_state()
        return int(record["credits"])

    def consume_user_credit(self, user_telegram_id: int) -> bool:
        """Deduct 1 exam credit from the candidate if available.

        Returns:
            `True` if 1 credit was deducted, `False` if the user has 0 credits.
        """
        record = self._ensure_user_record(user_telegram_id)
        current = int(record.get("credits", 0))
        if current < 1:
            return False

        record["credits"] = current - 1
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._state["credit_history"].append(
            {
                "user_telegram_id": int(user_telegram_id),
                "delta": -1,
                "new_balance": record["credits"],
                "reason": "exam_consumption",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_state()
        return True

    # -------------------------------------------------------------------------
    # 2. Tier 1: P2P Card Receipt Orders & Admin Approval
    # -------------------------------------------------------------------------

    def create_p2p_receipt_order(
        self,
        user_telegram_id: int,
        full_name: str,
        tariff_code: str,
        receipt_file_id: str | None = None,
        amount_uzs: int | None = None,
        credits: int = 1,
    ) -> dict[str, Any]:
        """Create a `PENDING` P2P card transfer order when a user submits a receipt."""
        self._ensure_user_record(user_telegram_id, full_name=full_name)
        tariff = TARIFF_CATALOG.get(tariff_code, TARIFF_CATALOG["full"])
        resolved_amount = int(amount_uzs if amount_uzs is not None else tariff["amount_uzs"])
        resolved_credits = int(credits if credits is not None else tariff.get("credits", 1))

        seq = len(self._state["orders"]) + 1
        year = datetime.now(timezone.utc).year
        order_id = f"P2P-{year}-{seq:04d}"
        while order_id in self._state["orders"]:
            seq += 1
            order_id = f"P2P-{year}-{seq:04d}"

        order: dict[str, Any] = {
            "order_id": order_id,
            "user_telegram_id": int(user_telegram_id),
            "full_name": full_name,
            "tariff_code": tariff_code if tariff_code in TARIFF_CATALOG else "full",
            "tariff_title_uz": tariff["title_uz"],
            "method": "P2P_CARD",
            "amount_uzs": resolved_amount,
            "credits": resolved_credits,
            "status": "PENDING",
            "receipt_file_id": receipt_file_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_reason": None,
        }
        self._state["orders"][order_id] = order
        self._save_state()
        return order

    def approve_p2p_order(
        self,
        order_id: str,
        admin_telegram_id: int = 0,
    ) -> dict[str, Any]:
        """Approve a P2P receipt order and credit the user's balance idempotently."""
        order = self._state["orders"].get(order_id)
        if order is None:
            raise ValueError(f"P2P order not found: {order_id}")

        # Idempotency guard: if already approved, return without double-crediting
        if order.get("status") == "APPROVED":
            return order

        order["status"] = "APPROVED"
        order["approved_by"] = int(admin_telegram_id)
        order["approved_at"] = datetime.now(timezone.utc).isoformat()

        new_balance = self.add_user_credits(
            user_telegram_id=int(order["user_telegram_id"]),
            credits=int(order.get("credits", 1)),
            reason=f"p2p_approved:{order_id}",
        )
        order["new_credit_balance"] = new_balance
        self._save_state()
        return order

    def reject_p2p_order(
        self,
        order_id: str,
        admin_telegram_id: int = 0,
        reason: str = "Chek tasdiqlanmadi",
    ) -> dict[str, Any]:
        """Reject a P2P receipt order without granting credits."""
        order = self._state["orders"].get(order_id)
        if order is None:
            raise ValueError(f"P2P order not found: {order_id}")

        if order.get("status") == "REJECTED":
            return order

        order["status"] = "REJECTED"
        order["rejected_by"] = int(admin_telegram_id)
        order["rejected_reason"] = reason
        order["rejected_at"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        return order

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Retrieve a payment order by its `order_id`."""
        return self._state["orders"].get(order_id)

    def list_pending_p2p_orders(self) -> list[dict[str, Any]]:
        """Return all P2P receipt orders currently awaiting admin verification."""
        return [
            order
            for order in self._state["orders"].values()
            if order.get("status") == "PENDING"
        ]

    # -------------------------------------------------------------------------
    # 3. Tier 2: Telegram Stars (XTR) Native Automated Payments
    # -------------------------------------------------------------------------

    def record_stars_payment(
        self,
        user_telegram_id: int,
        full_name: str,
        tariff_code: str,
        stars_amount: int,
        telegram_charge_id: str,
        credits: int = 1,
    ) -> dict[str, Any]:
        """Record a verified Telegram Stars (`XTR`) payment and grant credits immediately."""
        self._ensure_user_record(user_telegram_id, full_name=full_name)

        # Idempotency check by telegram_charge_id
        existing = self._state["stars_transactions"].get(telegram_charge_id)
        if existing is not None:
            return existing

        tariff = TARIFF_CATALOG.get(tariff_code, TARIFF_CATALOG["full"])
        new_balance = self.add_user_credits(
            user_telegram_id=int(user_telegram_id),
            credits=int(credits),
            reason=f"telegram_stars:{telegram_charge_id}",
        )

        tx: dict[str, Any] = {
            "transaction_id": f"XTR-{len(self._state['stars_transactions']) + 1:04d}",
            "user_telegram_id": int(user_telegram_id),
            "full_name": full_name,
            "tariff_code": tariff_code if tariff_code in TARIFF_CATALOG else "full",
            "tariff_title_uz": tariff["title_uz"],
            "method": "TELEGRAM_STARS",
            "currency": "XTR",
            "stars_amount": int(stars_amount),
            "telegram_charge_id": telegram_charge_id,
            "credits": int(credits),
            "new_credit_balance": new_balance,
            "status": "COMPLETED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._state["stars_transactions"][telegram_charge_id] = tx
        self._save_state()
        return tx

    # -------------------------------------------------------------------------
    # 4. Tier 3A: Click Merchant Webhook (Prepare / Complete with MD5)
    # -------------------------------------------------------------------------

    def handle_click_webhook(
        self,
        payload: dict[str, Any],
        enable_override: bool | None = None,
    ) -> dict[str, Any]:
        """Process Click Shop API `Prepare` (`action=0`) and `Complete` (`action=1`) webhooks.

        Remains dormant when `settings.ENABLE_CLICK_PAYME` is `False` unless `enable_override=True`.
        """
        enabled = enable_override if enable_override is not None else settings.ENABLE_CLICK_PAYME
        if not enabled:
            return {
                "error": -1,
                "error_note": (
                    "Click/Payme Merchant is disabled (ENABLE_CLICK_PAYME=False). "
                    "Use P2P Card or Telegram Stars."
                ),
            }

        click_trans_id = payload.get("click_trans_id", "")
        service_id = payload.get("service_id", settings.CLICK_SERVICE_ID)
        merchant_trans_id = str(payload.get("merchant_trans_id", ""))
        merchant_prepare_id = payload.get("merchant_prepare_id")
        amount = payload.get("amount", 0)
        action = int(payload.get("action", 0))
        sign_time = str(payload.get("sign_time", ""))
        sign_string = str(payload.get("sign_string", ""))

        expected_sign = compute_click_sign_string(
            click_trans_id=click_trans_id,
            service_id=service_id,
            secret_key=settings.CLICK_SECRET_KEY,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            action=action,
            sign_time=sign_time,
            merchant_prepare_id=merchant_prepare_id if action == 1 else None,
        )

        if not sign_string or not hmac.compare_digest(expected_sign.lower(), sign_string.lower()):
            return {
                "error": -1,
                "error_note": "SIGN CHECK FAILED!",
            }

        if int(payload.get("error", 0)) < 0:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": merchant_prepare_id or 0,
                "error": -9,
                "error_note": "Transaction cancelled",
            }

        click_txs = self._state["click_transactions"]
        if action == 0:
            prepare_id = len(click_txs) + 1
            click_txs[merchant_trans_id] = {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": prepare_id,
                "amount": float(amount),
                "status": "PREPARED",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save_state()
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": prepare_id,
                "error": 0,
                "error_note": "Success",
            }

        if action == 1:
            tx_record = click_txs.get(merchant_trans_id, {})
            resolved_prepare_id = (
                merchant_prepare_id
                if merchant_prepare_id is not None
                else tx_record.get("merchant_prepare_id", 1)
            )

            if tx_record.get("status") != "COMPLETED":
                user_id = self._resolve_user_id_from_merchant_trans(merchant_trans_id, payload)
                if user_id is not None:
                    self.add_user_credits(
                        user_telegram_id=user_id,
                        credits=1,
                        reason=f"click:{click_trans_id}",
                    )
                if merchant_trans_id in self._state["orders"]:
                    self._state["orders"][merchant_trans_id]["status"] = "APPROVED"

                click_txs[merchant_trans_id] = {
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": resolved_prepare_id,
                    "amount": float(amount),
                    "status": "COMPLETED",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                self._save_state()

            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": resolved_prepare_id,
                "error": 0,
                "error_note": "Success",
            }

        return {
            "error": -3,
            "error_note": f"Unknown Click action: {action}",
        }

    def _resolve_user_id_from_merchant_trans(
        self,
        merchant_trans_id: str,
        payload: dict[str, Any],
    ) -> int | None:
        """Resolve a candidate `user_telegram_id` from a Click/Payme order reference."""
        if "user_telegram_id" in payload:
            try:
                return int(payload["user_telegram_id"])
            except (TypeError, ValueError):
                pass

        order = self._state["orders"].get(merchant_trans_id)
        if order and "user_telegram_id" in order:
            return int(order["user_telegram_id"])

        if merchant_trans_id.isdigit():
            return int(merchant_trans_id)

        for part in merchant_trans_id.replace(":", "_").replace("-", "_").split("_"):
            if part.isdigit() and len(part) >= 5:
                return int(part)

        return None

    # -------------------------------------------------------------------------
    # 5. Tier 3B: Payme Merchant JSON-RPC 2.0 Handler
    # -------------------------------------------------------------------------

    def handle_payme_jsonrpc(
        self,
        payload: dict[str, Any],
        auth_header: str | None = None,
        enable_override: bool | None = None,
    ) -> dict[str, Any]:
        """Handle Payme Merchant API JSON-RPC 2.0 requests.

        Remains dormant when `settings.ENABLE_CLICK_PAYME` is `False` unless `enable_override=True`.
        """
        rpc_id = payload.get("id")
        enabled = enable_override if enable_override is not None else settings.ENABLE_CLICK_PAYME
        if not enabled:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32400,
                    "message": "Payme Merchant is disabled (ENABLE_CLICK_PAYME=False)",
                },
            }

        if not verify_payme_basic_auth(auth_header):
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32504,
                    "message": "Insufficient privilege to perform this method.",
                },
            }

        method = payload.get("method", "")
        params = payload.get("params") or {}
        payme_txs = self._state["payme_transactions"]
        now_ms = int(time.time() * 1000)

        if method == "CheckPerformTransaction":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {"allow": True},
            }

        if method == "CreateTransaction":
            payme_id = str(params.get("id", f"payme_{now_ms}"))
            tx = payme_txs.get(payme_id)
            if tx is None:
                tx = {
                    "payme_id": payme_id,
                    "transaction": f"ORD-{len(payme_txs) + 1:04d}",
                    "amount_tiyin": int(params.get("amount", 0)),
                    "account": params.get("account", {}),
                    "create_time": int(params.get("time", now_ms)),
                    "perform_time": 0,
                    "cancel_time": 0,
                    "state": 1,
                    "reason": None,
                }
                payme_txs[payme_id] = tx
                self._save_state()
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "create_time": tx["create_time"],
                    "transaction": tx["transaction"],
                    "state": tx["state"],
                },
            }

        if method == "PerformTransaction":
            payme_id = str(params.get("id", ""))
            tx = payme_txs.get(payme_id)
            if tx is None:
                tx = {
                    "payme_id": payme_id,
                    "transaction": f"ORD-{len(payme_txs) + 1:04d}",
                    "amount_tiyin": int(params.get("amount", 0)),
                    "account": params.get("account", {}),
                    "create_time": now_ms,
                    "perform_time": 0,
                    "cancel_time": 0,
                    "state": 1,
                    "reason": None,
                }
                payme_txs[payme_id] = tx

            if tx["state"] != 2:
                tx["state"] = 2
                tx["perform_time"] = now_ms
                account = tx.get("account") or {}
                order_ref = str(
                    account.get("order_id")
                    or account.get("user_telegram_id")
                    or account.get("user_id")
                    or ""
                )
                user_id = self._resolve_user_id_from_merchant_trans(order_ref, account)
                if user_id is not None:
                    self.add_user_credits(
                        user_telegram_id=user_id,
                        credits=1,
                        reason=f"payme:{payme_id}",
                    )
                self._save_state()

            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "transaction": tx["transaction"],
                    "perform_time": tx["perform_time"],
                    "state": tx["state"],
                },
            }

        if method == "CheckTransaction":
            payme_id = str(params.get("id", ""))
            tx = payme_txs.get(payme_id)
            if tx is None:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -31003,
                        "message": "Transaction not found",
                    },
                }
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "create_time": tx["create_time"],
                    "perform_time": tx.get("perform_time", 0),
                    "cancel_time": tx.get("cancel_time", 0),
                    "transaction": tx["transaction"],
                    "state": tx["state"],
                    "reason": tx.get("reason"),
                },
            }

        if method == "CancelTransaction":
            payme_id = str(params.get("id", ""))
            tx = payme_txs.get(payme_id)
            if tx is None:
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -31003,
                        "message": "Transaction not found",
                    },
                }
            if tx["state"] > 0:
                tx["state"] = -1 if tx["state"] == 1 else -2
                tx["cancel_time"] = now_ms
                tx["reason"] = int(params.get("reason", 1))
                self._save_state()
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "transaction": tx["transaction"],
                    "cancel_time": tx["cancel_time"],
                    "state": tx["state"],
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }

    # -------------------------------------------------------------------------
    # 6. Platform Revenue & Usage Statistics (Admin Panel)
    # -------------------------------------------------------------------------

    def get_platform_stats(self) -> dict[str, Any]:
        """Compute real-time platform statistics for the `/admin` dashboard and API."""
        users = self._state["users"]
        orders = list(self._state["orders"].values())
        stars_txs = list(self._state["stars_transactions"].values())

        total_users = len(users)
        total_credits_balance = sum(int(u.get("credits", 0)) for u in users.values())

        pending_p2p = [o for o in orders if o.get("status") == "PENDING"]
        approved_p2p = [o for o in orders if o.get("status") == "APPROVED"]
        rejected_p2p = [o for o in orders if o.get("status") == "REJECTED"]

        total_revenue_uzs = sum(int(o.get("amount_uzs", 0)) for o in approved_p2p)
        total_revenue_stars = sum(int(t.get("stars_amount", 0)) for t in stars_txs)

        return {
            "total_users": total_users,
            "total_credits_balance": total_credits_balance,
            "pending_p2p_count": len(pending_p2p),
            "approved_p2p_count": len(approved_p2p),
            "rejected_p2p_count": len(rejected_p2p),
            "stars_payments_count": len(stars_txs),
            "total_revenue_uzs": total_revenue_uzs,
            "total_revenue_stars": total_revenue_stars,
        }


_billing_ledger_singleton: BillingLedgerService | None = None


def get_billing_ledger_service() -> BillingLedgerService:
    """Return the singleton `BillingLedgerService` instance."""
    global _billing_ledger_singleton
    if _billing_ledger_singleton is None:
        _billing_ledger_singleton = BillingLedgerService()
    return _billing_ledger_singleton


__all__ = [
    "TARIFF_CATALOG",
    "BillingLedgerService",
    "compute_click_sign_string",
    "get_billing_ledger_service",
    "verify_payme_basic_auth",
]
