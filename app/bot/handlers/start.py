"""Telegram Bot Start, Help, Mock, and Profile Command Handlers (`aiogram 3.x`)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.exam_kb import (
    build_exam_type_keyboard,
    build_main_menu_keyboard,
)
from app.bot.states.exam_states import ExamSessionStates
from app.core.config import settings

router = Router(name="start_router")


WELCOME_TEXT_UZ = (
    "🎓 <b>IELTS &amp; CEFR Mock AI</b> platformasiga xush kelibsiz!\n\n"
    "Ushbu tizim orqali siz xalqaro <b>IELTS Academic (0.0 – 9.0 Band)</b> hamda "
    "O'zbekiston milliy <b>BBA Multi-Level CEFR (B1, B2, C1 — 0–75 shkala)</b> "
    "formatida to'liq 4 ta ko'nikma bo'yicha sinov (Mock) topshirishingiz mumkin:\n\n"
    "🎧 <b>Listening &amp; Reading:</b> 40 tadan savol (Telegram Mini App orqali)\n"
    "✍️ <b>Writing (Task 1 &amp; Task 2):</b> Matn yoki daftar rasmidan (Vision OCR) AI tahlil\n"
    "🎙 <b>Speaking (Part 1, 2, 3):</b> Ovozli xabar (.ogg) orqali Whisper STT + AI imtihon\n"
    "📄 <b>Natija:</b> 2-3 sahifali <b>PDF Sertifikat + Xatolar Daftari + C1 Band Booster</b>\n\n"
    "⚖️ <i>Eslatma: Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool). "
    "Rasmiy Cambridge, IDP, British Council yoki BBA sertifikati hisoblanmaydi.</i>\n\n"
    "👇 Quyidagi menyudan imtihon turini tanlang:"
)

HELP_TEXT_UZ = (
    "ℹ️ <b>Platformadan foydalanish bo'yicha yo'riqnoma:</b>\n\n"
    "1️⃣ <b>/mock</b> buyrug'ini bosing va <b>IELTS Academic</b> yoki <b>Milliy CEFR (Multi-Level)</b> formatini tanlang.\n"
    "2️⃣ <b>Rejimni tanlang:</b>\n"
    "   • 🏆 <b>To'liq 4-Skill Mock:</b> Listening + Reading + Writing + Speaking\n"
    "   • ✍️ <b>Faqat Writing:</b> Task 1 va Task 2 insho tahlili\n"
    "   • 🎙 <b>Faqat Speaking:</b> Part 1, Part 2 (Cue Card) va Part 3 ovozli tahlili\n"
    "3️⃣ <b>Writing bo'limida:</b> Inshoni matn ko'rinishida yozib yuborishingiz yoki "
    "daftarga qo'lda yozilgan insho <b>rasmini (Photo)</b> yuborishingiz mumkin (Vision OCR o'qiydi).\n"
    "4️⃣ <b>Speaking bo'limida:</b> Har bir qism savollariga <b>ovozli xabar (Voice .ogg)</b> "
    "yoki matn yuboring.\n"
    "5️⃣ Yakunda tizim sizga QR-kodli <b>PDF Sertifikat va Xatolar Daftari</b> faylini yuboradi!\n\n"
    "Asosiy buyruqlar:\n"
    "• /start — Asosiy menyu\n"
    "• /mock — Yangi imtihon boshlash\n"
    "• /profile — Profil va tariflar\n"
    "• /help — Yordam"
)


def _format_profile_text(user_id: int, full_name: str) -> str:
    """Format candidate profile and tariff pricing summary in Uzbek."""
    return (
        "👤 <b>Nomzod Profili va Tariflar</b>\n\n"
        f"• <b>Ism:</b> {full_name}\n"
        f"• <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"• <b>Bepul sinov (Demo) imkoniyatlari:</b> {settings.FREE_TRIAL_CREDITS} ta\n\n"
        "💳 <b>Tariflar (Click / Payme orqali):</b>\n"
        f"• 🏆 To'liq 4-Skill Mock (L+R+W+S + PDF): <b>{settings.PRICE_FULL_MOCK_UZS:,} so'm</b>\n"
        f"• ✍️ Faqat Writing (Task 1 + Task 2 + OCR + PDF): <b>{settings.PRICE_WRITING_ONLY_UZS:,} so'm</b>\n"
        f"• 🎙 Faqat Speaking (Part 1-3 + Whisper + PDF): <b>{settings.PRICE_SPEAKING_ONLY_UZS:,} so'm</b>\n\n"
        "Sinovni hoziroq boshlash uchun /mock buyrug'ini bosing yoki quyidagi tugmani tanlang:"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle `/start` command: reset session state and show the main menu."""
    from aiogram.types import MenuButtonWebApp, WebAppInfo
    from app.bot.keyboards.exam_kb import _is_public_https_url, _resolve_webapp_url

    await state.clear()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    resolved_webapp = _resolve_webapp_url()
    if message.bot and _is_public_https_url(resolved_webapp):
        try:
            await message.bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="📱 Imtihon (App)",
                    web_app=WebAppInfo(url=resolved_webapp),
                ),
            )
        except Exception:
            pass
    await message.answer(
        text=WELCOME_TEXT_UZ,
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle `/help` command."""
    await message.answer(
        text=HELP_TEXT_UZ,
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    """Handle inline Help button callback."""
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text=HELP_TEXT_UZ,
            reply_markup=build_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.message(Command("mock"))
async def cmd_mock(message: Message, state: FSMContext) -> None:
    """Handle `/mock` command: prompt candidate to select IELTS or CEFR."""
    await state.clear()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    await message.answer(
        text="🎯 <b>Imtihon formatini tanlang:</b>\n\nQaysi yo'nalishda Mock topshirmoqchisiz?",
        reply_markup=build_exam_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:choose_exam")
async def cb_choose_exam(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle back button to return to exam type selection."""
    await callback.answer()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    if callback.message:
        await callback.message.answer(
            text="🎯 <b>Imtihon formatini tanlang:</b>\n\nQaysi yo'nalishda Mock topshirmoqchisiz?",
            reply_markup=build_exam_type_keyboard(),
            parse_mode="HTML",
        )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    """Handle `/profile` command."""
    user = message.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"
    await message.answer(
        text=_format_profile_text(user_id=user_id, full_name=full_name),
        reply_markup=build_exam_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:profile")
async def cb_profile(callback: CallbackQuery) -> None:
    """Handle inline Profile button callback."""
    await callback.answer()
    user = callback.from_user
    user_id = user.id if user else 0
    full_name = user.full_name if user else "Candidate"
    if callback.message:
        await callback.message.answer(
            text=_format_profile_text(user_id=user_id, full_name=full_name),
            reply_markup=build_exam_type_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "menu:webapp_local")
async def cb_webapp_local(callback: CallbackQuery) -> None:
    """Handle Mini App button when running locally on localhost (before HTTPS domain setup)."""
    await callback.answer("Brauzerda http://localhost:8080/webapp manzilini oching!", show_alert=False)
    if callback.message:
        await callback.message.answer(
            text=(
                "🖥 <b>Interaktiv Mini App (WebApp) — Lokal Test Rejimi</b>\n\n"
                "Kompyuteringizdagi brauzer orqali quyidagi havolani oching:\n"
                "👉 <a href='http://localhost:8080/webapp'>http://localhost:8080/webapp</a>\n\n"
                "<i>Eslatma: Telegram ichida WebApp oyna bo'lib ochilishi uchun <code>.env</code> fayldagi "
                "<code>WEBAPP_URL</code> ga haqiqiy HTTPS manzil (masalan, Cloudflare Pages / Vercel / ngrok) "
                "yoziladi. Ungacha brauzerda <code>http://localhost:8080/webapp</code> orqali yoki "
                "bevosita botning o'zida imtihon topshirishingiz mumkin!</i>"
            ),
            reply_markup=build_exam_type_keyboard(),
            parse_mode="HTML",
        )


__all__ = ["router"]
