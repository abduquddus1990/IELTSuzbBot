"""Telegram Bot Hybrid Monetization & Admin Panel Handlers (`aiogram 3.x`).

Implements the 3-Tier Uzbekistan EdTech Monetization & Admin Architecture:
1. Tier 1 (P2P Uzcard/Humo Card Transfer + Receipt Screenshot Verification):
   - `/buy` command and `menu:buy` callback displaying user credit balance and tariffs.
   - `pay_p2p:<tariff_code>` displays 1-click copyable card number (`<code>...</code>`),
     card holder, bank name, exact UZS price, and transitions to `PaymentFlowStates.waiting_for_receipt`.
   - Receipt handler (`F.photo | F.document | F.text`) creates a `PENDING` order in
     `BillingLedgerService` and dispatches 1-click `[✅ Tasdiqlash (+1 Mock)]` / `[❌ Rad etish]`
     inline buttons to all admins (and to the current chat when `settings.DEBUG` is True).
   - `admin_pay:approve:<order_id>` and `admin_pay:reject:<order_id>` idempotently update
     the ledger, edit the admin card, and notify the candidate immediately.
2. Tier 2 (Telegram Stars `XTR` Native Automated Payments):
   - `pay_stars:<tariff_code>` sends a native `XTR` invoice (`provider_token=""`, `currency="XTR"`).
   - `pre_checkout_query` answers `ok=True`.
   - `F.successful_payment` records the Stars transaction and grants exam credits automatically.
3. Tier 3 (Dormant Click/Payme Info + `/admin` Dashboard & `/grant` Command):
   - `/admin` and `admin_panel:*` callbacks show real-time statistics, pending P2P checks,
     and 1-click `+3` test credit self-grant.
   - `/grant <telegram_id> <credits>` grants bonus exam credits to any candidate.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from app.core.config import settings
from app.services.payment_service import (
    TARIFF_CATALOG,
    get_billing_ledger_service,
)

logger = logging.getLogger(__name__)

router = Router(name="billing_and_admin_router")


# =====================================================================
# 1. FSM STATES FOR P2P RECEIPT UPLOAD
# =====================================================================


class PaymentFlowStates(StatesGroup):
    """FSM state group for P2P card transfer receipt upload workflow."""

    waiting_for_receipt = State()


# =====================================================================
# 2. INLINE KEYBOARD BUILDERS
# =====================================================================


def build_payment_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Build hybrid payment tariffs keyboard (P2P Card + Telegram Stars XTR + Click/Payme)."""
    rows: list[list[InlineKeyboardButton]] = []

    if settings.ENABLE_P2P_CARD:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💳 Karta (P2P): To'liq Mock — {settings.PRICE_FULL_MOCK_UZS:,} so'm",
                    callback_data="pay_p2p:full",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💳 Karta (P2P): Writing — {settings.PRICE_WRITING_ONLY_UZS:,} so'm",
                    callback_data="pay_p2p:writing",
                ),
                InlineKeyboardButton(
                    text=f"💳 Karta (P2P): Speaking — {settings.PRICE_SPEAKING_ONLY_UZS:,} so'm",
                    callback_data="pay_p2p:speaking",
                ),
            ]
        )

    if settings.ENABLE_TELEGRAM_STARS:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"⭐ Telegram Stars: To'liq Mock ({settings.PRICE_FULL_MOCK_STARS} XTR)",
                    callback_data="pay_stars:full",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"⭐ Stars: Writing ({settings.PRICE_WRITING_ONLY_STARS} XTR)",
                    callback_data="pay_stars:writing",
                ),
                InlineKeyboardButton(
                    text=f"⭐ Stars: Speaking ({settings.PRICE_SPEAKING_ONLY_STARS} XTR)",
                    callback_data="pay_stars:speaking",
                ),
            ]
        )

    if settings.ENABLE_CLICK_PAYME:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🟢 Click / Payme Avtomatik To'lov",
                    callback_data="pay_click_payme:info",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="🎯 Imtihonni boshlash (/mock)",
                callback_data="menu:choose_exam",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_admin_receipt_approval_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Build 1-click Admin Approve / Reject inline keyboard for a P2P receipt order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash (+1 Mock)",
                    callback_data=f"admin_pay:approve:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"admin_pay:reject:{order_id}",
                ),
            ]
        ]
    )


def build_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Build interactive Admin Panel (`/admin`) inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Statistikani yangilash",
                    callback_data="admin_panel:refresh",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Kutilayotgan P2P Cheklar",
                    callback_data="admin_panel:pending",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 O'zimga +3 Test Kredit qo'shish",
                    callback_data="admin_panel:self_grant",
                )
            ],
        ]
    )


# =====================================================================
# 3. HELPER FORMATTERS & ACCESS CHECKS
# =====================================================================


def _is_admin_user(user_id: int) -> bool:
    """Return True if the user is in `ADMIN_TELEGRAM_IDS` or if `DEBUG` mode is enabled."""
    return bool(settings.DEBUG or user_id in settings.admin_ids_list)


def _format_buy_menu_text(user_id: int, full_name: str) -> str:
    """Format the `/buy` tariff and balance overview message in Uzbek."""
    ledger = get_billing_ledger_service()
    credits = ledger.get_user_credits(user_id)

    methods_summary: list[str] = []
    if settings.ENABLE_P2P_CARD:
        methods_summary.append(
            "1️⃣ <b>Karta orqali (P2P Uzcard/Humo):</b> Karta raqamiga o'tkazib, chek skrinshotini "
            "yuborasiz — Admin 1 ta tugma bilan tasdiqlaydi."
        )
    if settings.ENABLE_TELEGRAM_STARS:
        methods_summary.append(
            "2️⃣ <b>Telegram Stars (XTR):</b> 100% avtomatik to'lov — to'lov o'tishi bilan "
            "imtihon krediti darhol hisobingizga qo'shiladi."
        )
    if settings.ENABLE_CLICK_PAYME:
        methods_summary.append(
            "3️⃣ <b>Click / Payme Merchant:</b> Rasmiy korporativ avtomatik to'lov tizimi."
        )

    methods_block = "\n".join(methods_summary)
    return (
        "💎 <b>IELTS &amp; CEFR Mock AI — To'lov va Tariflar Bo'limi</b>\n\n"
        f"👤 <b>Nomzod:</b> {full_name} (<code>{user_id}</code>)\n"
        f"🎟 <b>Mavjud imtihon kreditlaringiz:</b> <b>{credits} ta</b>\n\n"
        "📋 <b>Tariflarimiz:</b>\n"
        f"• 🏆 <b>To'liq 4-Skill Mock (L+R+W+S + PDF):</b> {settings.PRICE_FULL_MOCK_UZS:,} so'm "
        f"/ {settings.PRICE_FULL_MOCK_STARS} ⭐\n"
        f"• ✍️ <b>Faqat Writing (Task 1 + Task 2 + OCR + PDF):</b> {settings.PRICE_WRITING_ONLY_UZS:,} so'm "
        f"/ {settings.PRICE_WRITING_ONLY_STARS} ⭐\n"
        f"• 🎙 <b>Faqat Speaking (Part 1-3 + Whisper + PDF):</b> {settings.PRICE_SPEAKING_ONLY_UZS:,} so'm "
        f"/ {settings.PRICE_SPEAKING_ONLY_STARS} ⭐\n\n"
        f"🛠 <b>Faol to'lov usullari:</b>\n{methods_block}\n\n"
        "👇 O'zingizga qulay to'lov usuli va tarifni tanlang:"
    )


def _format_admin_dashboard_text(stats: dict[str, Any]) -> str:
    """Format the `/admin` dashboard statistics message."""
    click_payme_badge = "🟢 Yoqilgan" if settings.ENABLE_CLICK_PAYME else "⚪ O'chirilgan (Dormant)"
    return (
        "🛡 <b>IELTS &amp; CEFR Mock AI — Admin Boshqaruv Paneli</b>\n\n"
        "📊 <b>Platforma Statistikasi (Real-Time):</b>\n"
        f"• 👥 Jami foydalanuvchilar: <b>{stats.get('total_users', 0)}</b>\n"
        f"• 🎟 Foydalanuvchilardagi jami kreditlar: <b>{stats.get('total_credits_balance', 0)}</b>\n"
        f"• ⏳ Kutilayotgan P2P cheklar: <b>{stats.get('pending_p2p_count', 0)}</b>\n"
        f"• ✅ Tasdiqlangan P2P to'lovlar: <b>{stats.get('approved_p2p_count', 0)}</b>\n"
        f"• ❌ Rad etilgan P2P cheklar: <b>{stats.get('rejected_p2p_count', 0)}</b>\n"
        f"• ⭐ Telegram Stars to'lovlar: <b>{stats.get('stars_payments_count', 0)}</b>\n\n"
        "💰 <b>Tushum (Revenue):</b>\n"
        f"• P2P Karta tushumi: <b>{stats.get('total_revenue_uzs', 0):,} so'm</b>\n"
        f"• Telegram Stars tushumi: <b>{stats.get('total_revenue_stars', 0)} XTR ⭐</b>\n\n"
        "⚙️ <b>To'lov Tizimlari Holati:</b>\n"
        f"• P2P Karta: <code>{settings.PAYMENT_CARD_NUMBER}</code> ({settings.PAYMENT_CARD_HOLDER})\n"
        f"• Click / Payme: <b>{click_payme_badge}</b>\n\n"
        "💡 <i>Istalgan foydalanuvchiga kredit berish uchun:</i>\n"
        "<code>/grant &lt;telegram_id&gt; &lt;kredit_soni&gt;</code>"
    )


# =====================================================================
# 4. /BUY COMMAND & TARIFF SELECTION HANDLERS
# =====================================================================


@router.message(Command("buy"))
async def cmd_buy(message: Message, state: FSMContext) -> None:
    """Handle `/buy` command: show candidate credit balance and hybrid payment options."""
    await state.clear()
    user = message.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"

    await message.answer(
        text=_format_buy_menu_text(user_id=user_id, full_name=full_name),
        reply_markup=build_payment_tariffs_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:buy")
async def cb_menu_buy(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle `menu:buy` inline button callback."""
    await callback.answer()
    await state.clear()
    user = callback.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"

    if callback.message:
        await callback.message.answer(
            text=_format_buy_menu_text(user_id=user_id, full_name=full_name),
            reply_markup=build_payment_tariffs_keyboard(),
            parse_mode="HTML",
        )


# =====================================================================
# 5. TIER 1: P2P CARD TRANSFER & RECEIPT UPLOAD WORKFLOW
# =====================================================================


@router.callback_query(F.data.startswith("pay_p2p:"))
async def cb_select_p2p_tariff(callback: CallbackQuery, state: FSMContext) -> None:
    """Display copyable Uzcard/Humo card details and wait for receipt screenshot."""
    await callback.answer()
    raw_code = (callback.data or "pay_p2p:full").split(":", 1)[1].strip().lower()
    tariff_code = raw_code if raw_code in TARIFF_CATALOG else "full"
    tariff = TARIFF_CATALOG[tariff_code]

    await state.set_state(PaymentFlowStates.waiting_for_receipt)
    await state.update_data(
        tariff_code=tariff_code,
        amount_uzs=tariff["amount_uzs"],
        credits=tariff.get("credits", 1),
    )

    if callback.message:
        await callback.message.answer(
            text=(
                "💳 <b>P2P Karta orqali to'lov (Uzcard / Humo)</b>\n\n"
                f"📘 <b>Tanlangan tarif:</b> {tariff['title_uz']}\n"
                f"💰 <b>To'lov summasi:</b> <b>{tariff['amount_uzs']:,} so'm</b>\n\n"
                "🏦 <b>To'lov rekvizitlari (nusxa olish uchun karta raqamiga bosing):</b>\n"
                f"• Karta raqami: <code>{settings.PAYMENT_CARD_NUMBER}</code>\n"
                f"• Karta egasi: <b>{settings.PAYMENT_CARD_HOLDER}</b> ({settings.PAYMENT_CARD_BANK})\n\n"
                "📸 <i>To'lovni amalga oshirgach, chek skrinshotini (Rasm yoki PDF fayl) "
                "shu yerga yuboring.</i>"
            ),
            parse_mode="HTML",
        )


@router.message(PaymentFlowStates.waiting_for_receipt, F.photo | F.document | F.text)
async def handle_p2p_receipt_submission(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Accept P2P receipt photo/document/text, create order, and send 1-click Approval to Admins."""
    data = await state.get_data()
    tariff_code = str(data.get("tariff_code", "full"))
    tariff = TARIFF_CATALOG.get(tariff_code, TARIFF_CATALOG["full"])

    user = message.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"

    receipt_file_id: str | None = None
    if message.photo:
        receipt_file_id = message.photo[-1].file_id
    elif message.document:
        receipt_file_id = message.document.file_id
    elif message.text:
        receipt_file_id = f"text_receipt:{message.text[:80]}"

    ledger = get_billing_ledger_service()
    order = ledger.create_p2p_receipt_order(
        user_telegram_id=user_id,
        full_name=full_name,
        tariff_code=tariff_code,
        receipt_file_id=receipt_file_id,
        amount_uzs=int(tariff["amount_uzs"]),
        credits=int(tariff.get("credits", 1)),
    )
    order_id = order["order_id"]

    await state.clear()

    await message.answer(
        text=(
            f"⏳ Chekingiz qabul qilindi (Buyurtma <b>#{order_id}</b>)!\n"
            "Admin tekshirib tasdiqlashi bilan sizga xabar boradi."
        ),
        parse_mode="HTML",
    )

    admin_caption = (
        "🆕 <b>YANGI P2P TO'LOV CHEKI!</b>\n\n"
        f"🆔 Buyurtma: <code>{order_id}</code>\n"
        f"👤 Nomzod: <b>{full_name}</b> (<code>{user_id}</code>)\n"
        f"📘 Tarif: <b>{tariff['title_uz']}</b>\n"
        f"💰 Summa: <b>{order['amount_uzs']:,} so'm</b>\n"
        f"🎟 Beriladigan kredit: <b>+{order['credits']} ta Mock</b>\n\n"
        "👇 To'lov tushgan bo'lsa, 1-click orqali tasdiqlang:"
    )
    approval_kb = build_admin_receipt_approval_keyboard(order_id=order_id)

    # Collect target admin chat IDs; in DEBUG mode also include current chat so owner can test 1-click approval
    target_chat_ids: list[int] = list(settings.admin_ids_list)
    if settings.DEBUG and message.chat and message.chat.id not in target_chat_ids:
        target_chat_ids.append(message.chat.id)

    for admin_chat_id in target_chat_ids:
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=admin_chat_id,
                    photo=message.photo[-1].file_id,
                    caption=admin_caption,
                    reply_markup=approval_kb,
                    parse_mode="HTML",
                )
            elif message.document:
                await bot.send_document(
                    chat_id=admin_chat_id,
                    document=message.document.file_id,
                    caption=admin_caption,
                    reply_markup=approval_kb,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=admin_chat_id,
                    text=admin_caption,
                    reply_markup=approval_kb,
                    parse_mode="HTML",
                )
        except Exception as exc:
            logger.debug("Could not deliver P2P receipt to admin %s: %s", admin_chat_id, exc)


@router.callback_query(F.data.startswith("admin_pay:"))
async def cb_admin_payment_decision(callback: CallbackQuery, bot: Bot) -> None:
    """Handle Admin 1-click `[✅ Tasdiqlash (+1 Mock)]` or `[❌ Rad etish]` callback."""
    admin_user = callback.from_user
    admin_id = admin_user.id if admin_user else 0

    if not _is_admin_user(admin_id):
        await callback.answer("⛔ Sizda admin huquqi yo'q!", show_alert=True)
        return

    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer("Noto'g'ri buyruq formati.", show_alert=True)
        return

    action = parts[1].strip().lower()
    order_id = parts[2].strip()
    ledger = get_billing_ledger_service()

    try:
        if action == "approve":
            order = ledger.approve_p2p_order(order_id=order_id, admin_telegram_id=admin_id)
            new_balance = ledger.get_user_credits(int(order["user_telegram_id"]))
            await callback.answer("✅ To'lov tasdiqlandi va kredit qo'shildi!")

            status_text = (
                f"✅ <b>TASDIQLANDI</b> — Buyurtma <code>{order_id}</code>\n"
                f"👤 Nomzod: <b>{order['full_name']}</b> (<code>{order['user_telegram_id']}</code>)\n"
                f"💰 Summa: <b>{order['amount_uzs']:,} so'm</b>\n"
                f"🎟 Yangi balans: <b>{new_balance} ta kredit</b>"
            )
            if callback.message:
                if callback.message.caption:
                    await callback.message.edit_caption(caption=status_text, parse_mode="HTML")
                else:
                    await callback.message.edit_text(text=status_text, parse_mode="HTML")

            try:
                await bot.send_message(
                    chat_id=int(order["user_telegram_id"]),
                    text=(
                        f"🎉 <b>To'lovingiz tasdiqlandi!</b> (Buyurtma <code>#{order_id}</code>)\n\n"
                        f"🎟 Hisobingizga <b>+{order.get('credits', 1)} ta Mock imtihon krediti</b> qo'shildi.\n"
                        f"📊 Jami mavjud kreditlaringiz: <b>{new_balance} ta</b>\n\n"
                        "👉 Imtihonni boshlash uchun /mock buyrug'ini bosing!"
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.debug("Could not notify candidate %s: %s", order["user_telegram_id"], exc)
            return

        if action == "reject":
            order = ledger.reject_p2p_order(
                order_id=order_id,
                admin_telegram_id=admin_id,
                reason="To'lov cheki tasdiqlanmadi",
            )
            await callback.answer("❌ Buyurtma rad etildi.")

            status_text = (
                f"❌ <b>RAD ETILDI</b> — Buyurtma <code>{order_id}</code>\n"
                f"👤 Nomzod: <b>{order['full_name']}</b> (<code>{order['user_telegram_id']}</code>)"
            )
            if callback.message:
                if callback.message.caption:
                    await callback.message.edit_caption(caption=status_text, parse_mode="HTML")
                else:
                    await callback.message.edit_text(text=status_text, parse_mode="HTML")

            try:
                await bot.send_message(
                    chat_id=int(order["user_telegram_id"]),
                    text=(
                        f"⚠️ <b>Chekingiz tasdiqlanmadi</b> (Buyurtma <code>#{order_id}</code>).\n"
                        "Iltimos, to'lov chekini qayta tekshirib /buy orqali yuboring."
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.debug("Could not notify candidate %s: %s", order["user_telegram_id"], exc)
            return

    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)


# =====================================================================
# 6. TIER 2: TELEGRAM STARS (XTR) AUTOMATED INVOICE & PAYMENT HANDLERS
# =====================================================================


@router.callback_query(F.data.startswith("pay_stars:"))
async def cb_send_stars_invoice(callback: CallbackQuery) -> None:
    """Send a native Telegram Stars (`XTR`) invoice with `provider_token=""`."""
    await callback.answer()
    raw_code = (callback.data or "pay_stars:full").split(":", 1)[1].strip().lower()
    tariff_code = raw_code if raw_code in TARIFF_CATALOG else "full"
    tariff = TARIFF_CATALOG[tariff_code]
    stars_amount = int(tariff["stars"])

    user = callback.from_user
    user_id = user.id if user else 0

    if callback.message:
        await callback.message.answer_invoice(
            title=f"IELTS & CEFR Mock AI — {tariff_code.upper()}",
            description=(
                f"{tariff['title_uz']} (+{tariff.get('credits', 1)} ta Mock imtihon krediti va PDF hisobot)"
            ),
            payload=f"stars:{tariff_code}:{user_id}",
            provider_token="",
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=tariff["title_uz"],
                    amount=stars_amount,
                )
            ],
        )


@router.pre_checkout_query()
async def handle_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    """Confirm Telegram Stars (`XTR`) pre-checkout query within 10 seconds."""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    """Record completed Telegram Stars (`XTR`) payment and grant exam credits immediately."""
    payment = message.successful_payment
    if payment is None:
        return

    payload_str = payment.invoice_payload or "stars:full:0"
    parts = payload_str.split(":")
    tariff_code = parts[1] if len(parts) > 1 and parts[1] in TARIFF_CATALOG else "full"
    tariff = TARIFF_CATALOG[tariff_code]

    user = message.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"

    ledger = get_billing_ledger_service()
    tx = ledger.record_stars_payment(
        user_telegram_id=user_id,
        full_name=full_name,
        tariff_code=tariff_code,
        stars_amount=int(payment.total_amount),
        telegram_charge_id=payment.telegram_payment_charge_id,
        credits=int(tariff.get("credits", 1)),
    )

    await message.answer(
        text=(
            "🌟 <b>Telegram Stars to'lovingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
            f"📘 Tarif: <b>{tariff['title_uz']}</b>\n"
            f"⭐ To'langan: <b>{tx['stars_amount']} XTR</b>\n"
            f"🎟 Yangi balans: <b>{tx['new_credit_balance']} ta imtihon krediti</b>\n\n"
            "👉 Hoziroq imtihonni boshlash uchun /mock buyrug'ini bosing!"
        ),
        parse_mode="HTML",
    )


# =====================================================================
# 7. TIER 3: CLICK/PAYME INFO & ADMIN PANEL (/ADMIN, /GRANT)
# =====================================================================


@router.callback_query(F.data == "pay_click_payme:info")
async def cb_click_payme_info(callback: CallbackQuery) -> None:
    """Show Click & Payme merchant integration details when `ENABLE_CLICK_PAYME=True`."""
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text=(
                "🟢 <b>Click &amp; Payme Merchant Avtomatik To'lov</b>\n\n"
                "Webhook endpointlar faol:\n"
                "• Click Prepare: <code>POST /api/v1/payments/click/prepare</code>\n"
                "• Click Complete: <code>POST /api/v1/payments/click/complete</code>\n"
                "• Payme JSON-RPC: <code>POST /api/v1/payments/payme</code>\n\n"
                "Shuningdek, P2P Karta yoki Telegram Stars orqali ham darhol to'lashingiz mumkin!"
            ),
            parse_mode="HTML",
        )


@router.message(Command("admin"))
async def cmd_admin_dashboard(message: Message) -> None:
    """Handle `/admin` command: show real-time platform statistics and management controls."""
    user = message.from_user
    user_id = user.id if user else 0

    if not _is_admin_user(user_id):
        await message.answer("⛔ Ushbu bo'lim faqat platforma administratorlari uchun.")
        return

    ledger = get_billing_ledger_service()
    stats = ledger.get_platform_stats()
    await message.answer(
        text=_format_admin_dashboard_text(stats),
        reply_markup=build_admin_dashboard_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("grant"))
async def cmd_grant_credits(message: Message) -> None:
    """Handle `/grant <telegram_id> <credits>` command to add bonus credits to a user."""
    user = message.from_user
    admin_id = user.id if user else 0

    if not _is_admin_user(admin_id):
        await message.answer("⛔ Sizda admin huquqi yo'q.")
        return

    parts = (message.text or "").strip().split()
    if len(parts) < 3 or not parts[1].lstrip("-").isdigit() or not parts[2].isdigit():
        await message.answer(
            text=(
                "ℹ️ <b>Foydalanuvchiga kredit qo'shish formati:</b>\n"
                "<code>/grant &lt;telegram_id&gt; &lt;kredit_soni&gt;</code>\n\n"
                f"Misol: <code>/grant {admin_id} 5</code>"
            ),
            parse_mode="HTML",
        )
        return

    target_user_id = int(parts[1])
    credits_to_add = int(parts[2])
    ledger = get_billing_ledger_service()
    new_balance = ledger.add_user_credits(
        user_telegram_id=target_user_id,
        credits=credits_to_add,
        reason=f"admin_cmd_grant_by_{admin_id}",
    )

    await message.answer(
        text=(
            f"✅ Foydalanuvchi <code>{target_user_id}</code> hisobiga "
            f"<b>+{credits_to_add} ta kredit</b> qo'shildi!\n"
            f"🎟 Yangi balans: <b>{new_balance} ta kredit</b>"
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_panel:"))
async def cb_admin_panel_actions(callback: CallbackQuery) -> None:
    """Handle `admin_panel:refresh`, `admin_panel:pending`, and `admin_panel:self_grant`."""
    user = callback.from_user
    admin_id = user.id if user else 0

    if not _is_admin_user(admin_id):
        await callback.answer("⛔ Sizda admin huquqi yo'q!", show_alert=True)
        return

    action = (callback.data or "admin_panel:refresh").split(":", 1)[1].strip().lower()
    ledger = get_billing_ledger_service()

    if action == "self_grant":
        new_balance = ledger.add_user_credits(
            user_telegram_id=admin_id,
            credits=3,
            reason="admin_self_grant",
        )
        await callback.answer(f"🎁 Hisobingizga +3 ta kredit qo'shildi! Jami: {new_balance}", show_alert=True)
        if callback.message:
            stats = ledger.get_platform_stats()
            await callback.message.edit_text(
                text=_format_admin_dashboard_text(stats),
                reply_markup=build_admin_dashboard_keyboard(),
                parse_mode="HTML",
            )
        return

    if action == "pending":
        pending_orders = ledger.list_pending_p2p_orders()
        await callback.answer()
        if not callback.message:
            return
        if not pending_orders:
            await callback.message.answer(
                "✅ Hozirda kutilayotgan (PENDING) P2P to'lov cheklari yo'q.",
                parse_mode="HTML",
            )
            return

        for order in pending_orders[:10]:
            await callback.message.answer(
                text=(
                    f"⏳ <b>Kutilayotgan Buyurtma #{order['order_id']}</b>\n"
                    f"👤 Nomzod: <b>{order['full_name']}</b> (<code>{order['user_telegram_id']}</code>)\n"
                    f"📘 Tarif: {order['tariff_title_uz']}\n"
                    f"💰 Summa: <b>{order['amount_uzs']:,} so'm</b>"
                ),
                reply_markup=build_admin_receipt_approval_keyboard(order["order_id"]),
                parse_mode="HTML",
            )
        return

    # Default: refresh stats
    await callback.answer("🔄 Statistika yangilandi")
    if callback.message:
        stats = ledger.get_platform_stats()
        await callback.message.edit_text(
            text=_format_admin_dashboard_text(stats),
            reply_markup=build_admin_dashboard_keyboard(),
            parse_mode="HTML",
        )


__all__ = [
    "PaymentFlowStates",
    "build_admin_dashboard_keyboard",
    "build_admin_receipt_approval_keyboard",
    "build_payment_tariffs_keyboard",
    "router",
]
