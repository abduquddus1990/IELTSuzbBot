---
name: monetization-and-admin
description: >-
  3-tier Hybrid Monetization Architecture for Uzbekistan EdTech:
  (1) P2P Uzcard/Humo Card Transfer + Receipt Screenshot Verification + Admin 1-Click Approval,
  (2) Telegram Stars (XTR) automated native payments (zero legal entity required),
  (3) Switchable Click (MD5 Prepare/Complete) & Payme (JSON-RPC) Merchant Webhooks for future YaTT/MChJ scale,
  plus Telegram Bot /admin Panel & User Credit Management.
---

# Hybrid Monetization (P2P Card + Telegram Stars XTR + Click/Payme) & Admin Skill

## 1. Tier 1: P2P Card Transfer + Receipt Screenshot (`No Legal Entity Required`)
- Display `PAYMENT_CARD_NUMBER`, `PAYMENT_CARD_HOLDER`, `PAYMENT_CARD_BANK`, and tariff price in UZS.
- Candidate transfers UZS via any banking app and sends the receipt photo/screenshot (`F.photo` or `F.document`).
- Create a pending payment record (`PaymentOrder`) with `method="P2P_CARD"`.
- Forward the receipt photo to all `ADMIN_TELEGRAM_IDS` with inline buttons:
  - `✅ Tasdiqlash (+1 Kredit)` (`admin_pay:approve:<order_id>:<user_telegram_id>:<credits>`)
  - `❌ Rad etish` (`admin_pay:reject:<order_id>:<user_telegram_id>`)
- When Admin clicks Approve, credit the user's account and notify the user immediately!

## 2. Tier 2: Telegram Stars (`XTR`) Automated Payment (`No Legal Entity Required`)
- Use `message.answer_invoice(..., currency="XTR", provider_token="", prices=[LabeledPrice(label=..., amount=stars_amount)])`.
- Handle `@router.pre_checkout_query()` with `await pre_checkout_query.answer(ok=True)`.
- Handle `@router.message(F.successful_payment)` to automatically grant exam credits and send confirmation.

## 3. Tier 3: Dormant / Switchable Click & Payme Merchant Webhooks (`ENABLE_CLICK_PAYME`)
- Controlled by `settings.ENABLE_CLICK_PAYME` (default `False`).
- **Click (`POST /api/v1/payments/click/prepare` & `/complete`):**
  - Verify MD5 `sign_string`:
    - Prepare (`action=0`): `md5(f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}")`
    - Complete (`action=1`): `md5(f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}")`
- **Payme (`POST /api/v1/payments/payme` JSON-RPC 2.0):**
  - Verify HTTP Basic Auth (`Paycom:<PAYME_KEY>`) and handle `CheckPerformTransaction`, `CreateTransaction`, `PerformTransaction`, `CheckTransaction`, `CancelTransaction`.

## 4. Admin Panel (`/admin`)
- Accessible to users in `settings.admin_ids_list` (or in `DEBUG=True` dev mode).
- View platform statistics (total users, completed mock exams, pending & approved payments).
- Grant bonus credits to any user (`/grant <telegram_id> <credits>`).
