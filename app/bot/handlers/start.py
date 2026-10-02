"""Telegram bot /start, /help, /mock, /stats and menu handlers (`aiogram 3.x`)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.exam_kb import build_exam_type_keyboard, build_main_menu_keyboard
from app.bot.states.exam_states import ExamSessionStates
from app.core.config import settings
from app.services import usage_limits

router = Router(name="start_router")


def _welcome_text() -> str:
    return (
        "🎓 <b>IELTS &amp; CEFR Mock AI</b> — free mock exams with instant AI feedback.\n\n"
        "📝 <b>Full mock</b> — Listening, Reading, Writing &amp; Speaking in a real exam layout, "
        "with a PDF report. Works on phones and computers.\n"
        "✍️ <b>Writing</b> and 🎙 <b>Speaking</b> practice — right here in the chat (text, photo or voice).\n\n"
        f"🆓 Everything is free. Limit: <b>{settings.DAILY_EXAM_LIMIT} AI-scored exams per day</b>; "
        "Listening &amp; Reading practice is unlimited.\n\n"
        "🇺🇿 <i>Bepul mock imtihonlar. Kuniga {limit} ta AI baholaydigan imtihon; Listening va Reading cheksiz.</i>\n\n"
        "⚖️ <i>Unofficial practice tool — not affiliated with IELTS, Cambridge, IDP, British Council or the "
        "Uzbekistan Knowledge Assessment Agency.</i>"
    ).replace("{limit}", str(settings.DAILY_EXAM_LIMIT))


HELP_TEXT = (
    "ℹ️ <b>How it works</b>\n\n"
    "1️⃣ <b>Full mock exam</b> — press the button to open the exam app. Listening is played once, "
    "each section is timed, and you get a PDF report at the end. On a computer, open the browser link.\n"
    "2️⃣ <b>Writing practice</b> — choose IELTS or CEFR, then send each task as text or a photo of your handwriting.\n"
    "3️⃣ <b>Speaking practice</b> — the examiner asks questions one by one; answer each with a voice message.\n\n"
    f"🆓 Free: {settings.DAILY_EXAM_LIMIT} AI-scored exams per day.\n\n"
    "Commands: /start — menu • /mock — choose an exam • /help — this message"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    from aiogram.types import MenuButtonWebApp, WebAppInfo

    from app.bot.keyboards.exam_kb import _is_public_https_url, _resolve_webapp_url

    await state.clear()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    resolved_webapp = _resolve_webapp_url()
    if message.bot and _is_public_https_url(resolved_webapp):
        try:
            await message.bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="📝 Mock Exam", web_app=WebAppInfo(url=resolved_webapp)),
            )
        except Exception:
            pass
    await message.answer(text=_welcome_text(), reply_markup=build_main_menu_keyboard(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(text=HELP_TEXT, reply_markup=build_main_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(text=HELP_TEXT, reply_markup=build_main_menu_keyboard(), parse_mode="HTML")


@router.message(Command("mock"))
async def cmd_mock(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    await message.answer(
        text="🎯 <b>Choose your exam:</b>",
        reply_markup=build_exam_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:choose_exam")
async def cb_choose_exam(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ExamSessionStates.choosing_exam_type)
    if callback.message:
        await callback.message.answer(
            text="🎯 <b>Choose your exam:</b>",
            reply_markup=build_exam_type_keyboard(),
            parse_mode="HTML",
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Admin-only usage overview for today."""
    if message.from_user is None or message.from_user.id not in settings.admin_ids_list:
        return
    totals = await usage_limits.daily_totals()
    await message.answer(
        "📈 <b>Today</b>\n"
        f"• AI-scored exams: <b>{totals.get('exam', 0)}</b> by {totals.get('exam_people', 0)} people\n"
        f"• Speaking transcriptions: <b>{totals.get('transcribe', 0)}</b>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:webapp_local")
async def cb_webapp_local(callback: CallbackQuery) -> None:
    await callback.answer("Open http://localhost:8080/webapp/ in your browser.", show_alert=True)


__all__ = ["router"]
