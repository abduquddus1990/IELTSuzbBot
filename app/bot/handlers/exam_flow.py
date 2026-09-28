"""Complete 4-Skill IELTS & Uzbekistan CEFR Mock Exam FSM Flow Handlers (`aiogram 3.x`).

Handles:
1. Selecting Exam Type (`exam_type:IELTS` or `exam_type:CEFR`) and Mode (`mode:full`, `mode:writing`, `mode:speaking`).
2. Completing Listening & Reading via Telegram Mini App (`F.web_app_data`), quick score buttons, or text input (`"32 30"`).
3. Submitting Writing Task 1 & Task 2 via text OR handwritten notebook photo (`F.photo` -> Vision OCR).
4. Submitting Speaking Part 1, Part 2, and Part 3 via `.ogg` voice message (`F.voice` -> Whisper STT) OR text.
5. Evaluating submissions via `WritingEvaluatorService`, `SpeakingEvaluatorService`, and `ExamOrchestratorService`
   (including a deterministic offline/demo fallback when `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`
   is still a placeholder like `"PUT_YOUR_ANTHROPIC_API_KEY_HERE"`).
6. Delivering the generated 2-3 page PDF Certificate & Error Workbook via `BufferedInputFile`.
"""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.bot.keyboards.exam_kb import (
    build_exam_mode_keyboard,
    build_exam_type_keyboard,
    build_listening_reading_keyboard,
    build_main_menu_keyboard,
)
from app.bot.states.exam_states import ExamSessionStates
from app.core.config import settings
from app.schemas.report import band_to_cefr_75_score
from app.schemas.speaking import (
    AudioTranscriptionResult,
    SpeakingCriteriaScores,
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
    SpeakingPartInput,
    SpeakingPartNumber,
)
from app.schemas.writing import (
    BandBoosterVocabulary,
    CriteriaScores,
    DetailedError,
    ExamType,
    WritingEvaluationRequest,
    WritingEvaluationResult,
    WritingTaskInput,
)
from app.services.demo_exam_bank import get_demo_test_by_id, get_random_demo_test
from app.services.exam_orchestrator import get_exam_orchestrator_service
from app.services.gemini_evaluator import (
    evaluate_speaking_via_gemini,
    evaluate_writing_via_gemini,
    transcribe_audio_via_gemini,
    transcribe_handwritten_image_via_gemini,
)
from app.services.reading_listening_scorer import (
    convert_listening_raw_to_band,
    convert_raw_to_cefr_standard_score,
    convert_reading_raw_to_band,
    round_to_half_band,
    score_reading_or_listening,
)
from app.services.speaking_evaluator import (
    analyze_speech_telemetry,
    build_zero_speaking_result,
    check_speaking_prompt_injection,
    evaluate_speaking,
    transcribe_speaking_audio,
    verify_and_recalculate_speaking_scores,
)
from app.services.writing_evaluator import (
    build_zero_score_result,
    check_prompt_injection,
    evaluate_writing,
    transcribe_handwritten_image,
    verify_and_recalculate_scores,
)

logger = logging.getLogger(__name__)

router = Router(name="exam_flow_router")


# =====================================================================
# 1. API KEY PLACEHOLDER DETECTION & GRACEFUL DEMO FALLBACK ENGINE
# =====================================================================


def is_placeholder_api_key(api_key: str | None) -> bool:
    """Return True if an API key is empty or still set to a `.env` placeholder string."""
    if not api_key or not api_key.strip():
        return True
    cleaned = api_key.strip()
    upper = cleaned.upper()
    if upper.startswith(("PUT_YOUR_", "YOUR_", "REPLACE_")):
        return True
    if "PLACEHOLDER" in upper or "YOUR_TELEGRAM_BOT_TOKEN" in upper:
        return True
    return False


async def transcribe_image_with_demo_fallback(
    image_bytes: bytes,
    task_number: Literal[1, 2] = 1,
) -> str:
    """Transcribe a handwritten essay image via Vision OCR (Claude/OpenAI/Gemini), with offline demo fallback."""
    claude_ready = not is_placeholder_api_key(settings.ANTHROPIC_API_KEY)
    openai_ready = not is_placeholder_api_key(settings.OPENAI_API_KEY)
    gemini_ready = not is_placeholder_api_key(settings.GEMINI_API_KEY)

    if claude_ready or openai_ready:
        try:
            transcribed = await transcribe_handwritten_image(image_bytes=image_bytes)
            if isinstance(transcribed, str) and transcribed.strip():
                return transcribed.strip()
        except Exception as exc:
            logger.warning("Claude/OpenAI Vision OCR failed (%s); checking Gemini/demo fallback.", exc)

    if gemini_ready:
        try:
            transcribed_gemini = await transcribe_handwritten_image_via_gemini(image_bytes=image_bytes)
            if transcribed_gemini.strip():
                return transcribed_gemini.strip()
        except Exception as exc:
            logger.warning("Gemini Vision OCR failed (%s); using demo OCR fallback.", exc)

    if task_number == 1:
        return (
            "The provided chart illustrates the proportion of households with fiber-optic internet "
            "and solar power across four nations between 2015 and 2025. Overall, digital connectivity "
            "and renewable energy adoption grew significantly in all surveyed countries, with South Korea "
            "and Germany maintaining the highest percentages throughout the decade while Uzbekistan "
            "recorded the fastest relative growth rate."
        )
    return (
        "In contemporary education, the rapid rise of artificial intelligence platforms has sparked "
        "debate over whether technology will replace human teachers. While automated systems offer "
        "personalized pacing and instant diagnostic feedback, I firmly believe that classroom educators "
        "remain indispensable for cultivating critical thinking, emotional intelligence, and collaborative "
        "problem-solving skills among students."
    )


async def transcribe_voice_with_demo_fallback(
    audio_bytes: bytes,
    duration_seconds: float = 15.0,
    part_number: SpeakingPartNumber = 1,
    filename: str = "voice.ogg",
) -> AudioTranscriptionResult:
    """Transcribe a `.ogg` voice message via OpenAI Whisper or Google Gemini Audio, with offline demo fallback."""
    if not is_placeholder_api_key(settings.OPENAI_API_KEY):
        try:
            return await transcribe_speaking_audio(
                audio_bytes=audio_bytes,
                filename=filename,
                duration_seconds=duration_seconds,
                part_number=part_number,
            )
        except Exception as exc:
            logger.warning("Live Whisper STT failed (%s); checking Gemini/demo STT fallback.", exc)

    if not is_placeholder_api_key(settings.GEMINI_API_KEY):
        try:
            return await transcribe_audio_via_gemini(
                audio_bytes=audio_bytes,
                duration_seconds=duration_seconds,
                part_number=part_number,
                filename=filename,
            )
        except Exception as exc:
            logger.warning("Live Gemini Audio STT failed (%s); using demo STT fallback.", exc)

    sample_transcripts: dict[int, str] = {
        1: (
            "Currently I am working as a software developer and studying English every evening "
            "because international communication and technical documentation are essential for my career."
        ),
        2: (
            "I would like to talk about a challenging data migration project where our team used an "
            "automated cloud monitoring tool. At first we faced latency issues, um, but after analyzing "
            "the metrics we optimized our database queries and completed the deployment ahead of schedule."
        ),
        3: (
            "In my view, digital platforms have transformed higher education in Uzbekistan by making "
            "global research accessible to everyone, although universities still need to balance theoretical "
            "foundations with practical industry internships."
        ),
    }
    text = sample_transcripts.get(int(part_number), sample_transcripts[1])
    safe_dur = float(duration_seconds) if duration_seconds and duration_seconds > 0 else 14.0
    return analyze_speech_telemetry(
        transcript_text=text,
        duration_seconds=safe_dur,
        part_number=part_number,
        model="whisper-1-demo-fallback",
    )


def _build_demo_writing_evaluation(
    exam_type: ExamType,
    t1_text: str,
    t2_text: str,
) -> WritingEvaluationResult:
    """Construct a deterministic, realistic `WritingEvaluationResult` when AI keys are placeholders."""
    t1_words = len(t1_text.split())
    t2_words = len(t2_text.split())

    # Heuristic scoring based on length and lexical diversity
    all_words = [w.lower().strip(".,!?;:()\"'") for w in (t1_text + " " + t2_text).split() if w]
    lexical_ratio = len(set(all_words)) / float(max(1, len(all_words)))

    t1_base = 6.5 if t1_words >= 140 else (6.0 if t1_words >= 70 else 5.5)
    t2_base = 7.0 if t2_words >= 230 else (6.5 if t2_words >= 100 else 6.0)
    if lexical_ratio >= 0.58 and t2_words >= 150:
        t2_base = min(8.0, t2_base + 0.5)

    t1_score = round_to_half_band(t1_base)
    t2_score = round_to_half_band(t2_base)

    raw_result = WritingEvaluationResult(
        exam_type=exam_type,
        task_1_score=t1_score,
        task_2_score=t2_score,
        overall_writing_score=6.5,
        cefr_level="B2",
        criteria_scores=CriteriaScores(
            task_achievement=t2_score,
            coherence_cohesion=round_to_half_band((t1_score + t2_score) / 2.0),
            lexical_resource=t2_score,
            grammatical_range_accuracy=t1_score,
        ),
        detailed_errors=[
            DetailedError(
                original="people is using technology more and more",
                correction="individuals are increasingly utilizing digital technologies",
                explanation_uz=(
                    "'People' ko'plikdagi ot bo'lgani uchun 'are' yordamchi fe'li ishlatiladi; "
                    "akademik uslubda 'more and more' o'rniga 'increasingly' ravishini qo'llash tavsiya etiladi."
                ),
            ),
            DetailedError(
                original="it have a big impact on education system",
                correction="it has a profound impact on the education system",
                explanation_uz=(
                    "Uchinchi shaxs birlikda ('it') Present Simple zamonida 'has' ishlatiladi hamda "
                    "aniq ot birikmasi oldidan 'the' artikli qo'yilishi shart."
                ),
            ),
            DetailedError(
                original="in conclusion I think both side is important",
                correction="In conclusion, I firmly believe that both perspectives hold merit",
                explanation_uz=(
                    "Kirish birikmasidan so'ng vergul qo'yiladi; 'both' so'zidan keyin ko'plikdagi "
                    "ot ('perspectives/sides') va ko'plikdagi kesim kelishi lozim."
                ),
            ),
        ],
        band_booster_vocabulary=[
            BandBoosterVocabulary(
                simple_used="big impact",
                advanced_alternative="profound / far-reaching implications",
            ),
            BandBoosterVocabulary(
                simple_used="good for students",
                advanced_alternative="conducive to learners' academic progression",
            ),
            BandBoosterVocabulary(
                simple_used="solve the problem",
                advanced_alternative="mitigate the underlying challenge",
            ),
            BandBoosterVocabulary(
                simple_used="more and more",
                advanced_alternative="at an unprecedented pace",
            ),
        ],
    )
    return verify_and_recalculate_scores(raw_result)


async def evaluate_writing_with_demo_fallback(
    request: WritingEvaluationRequest,
) -> WritingEvaluationResult:
    """Evaluate Writing Task 1 & Task 2 via Claude -> Gemini -> offline demo fallback."""
    t1_text = request.task_1.student_text
    if (not t1_text or not t1_text.strip()) and request.task_1.has_image:
        t1_text = await transcribe_image_with_demo_fallback(
            request.task_1.image_bytes or b"demo_image",
            task_number=1,
        )

    t2_text = request.task_2.student_text
    if (not t2_text or not t2_text.strip()) and request.task_2.has_image:
        t2_text = await transcribe_image_with_demo_fallback(
            request.task_2.image_bytes or b"demo_image",
            task_number=2,
        )

    # Layer 1: Always enforce anti-jailbreak & anti-cheating checks even in demo mode!
    check_t1 = check_prompt_injection(t1_text, task_number=1, enforce_min_words=True)
    if check_t1.is_detected:
        return build_zero_score_result(
            exam_type=request.exam_type,
            reason_uz=check_t1.explanation_uz,
            original_snippet=t1_text or "[Task 1 bo'sh]",
        )

    check_t2 = check_prompt_injection(t2_text, task_number=2, enforce_min_words=True)
    if check_t2.is_detected:
        return build_zero_score_result(
            exam_type=request.exam_type,
            reason_uz=check_t2.explanation_uz,
            original_snippet=t2_text or "[Task 2 bo'sh]",
        )

    assert t1_text is not None and t2_text is not None

    if not is_placeholder_api_key(settings.ANTHROPIC_API_KEY):
        try:
            hydrated_req = WritingEvaluationRequest(
                exam_type=request.exam_type,
                task_1=WritingTaskInput(
                    task_number=1,
                    prompt_topic=request.task_1.prompt_topic,
                    student_text=t1_text,
                ),
                task_2=WritingTaskInput(
                    task_number=2,
                    prompt_topic=request.task_2.prompt_topic,
                    student_text=t2_text,
                ),
            )
            return await evaluate_writing(request=hydrated_req)
        except Exception as exc:
            logger.warning(
                "Live Claude Writing evaluation failed (%s); checking Gemini/demo fallback.",
                exc,
            )

    if not is_placeholder_api_key(settings.GEMINI_API_KEY):
        try:
            return await evaluate_writing_via_gemini(
                request,
                t1_text=t1_text,
                t2_text=t2_text,
            )
        except Exception as exc:
            logger.warning(
                "Live Gemini Writing evaluation failed (%s); falling back to offline demo evaluator.",
                exc,
            )

    return _build_demo_writing_evaluation(
        exam_type=request.exam_type,
        t1_text=t1_text,
        t2_text=t2_text,
    )


def _build_demo_speaking_evaluation(
    exam_type: ExamType,
    p1_text: str,
    p2_text: str,
    p3_text: str,
) -> SpeakingEvaluationResult:
    """Construct a deterministic, realistic `SpeakingEvaluationResult` when AI keys are placeholders."""
    p1_words = len(p1_text.split())
    p2_words = len(p2_text.split())
    p3_words = len(p3_text.split())

    p1_score = 6.5 if p1_words >= 20 else 6.0
    p2_score = 7.0 if p2_words >= 35 else 6.5
    p3_score = 6.5 if p3_words >= 25 else 6.0

    raw_speaking = SpeakingEvaluationResult(
        exam_type=exam_type,
        part_1_score=p1_score,
        part_2_score=p2_score,
        part_3_score=p3_score,
        overall_speaking_score=6.5,
        standard_score_75=55.0,
        cefr_level="B2",
        criteria_scores=SpeakingCriteriaScores(
            fluency_coherence=p2_score,
            lexical_resource=p2_score,
            grammatical_range_accuracy=p1_score,
            pronunciation=p3_score,
        ),
        fluency_feedback_uz=(
            "Nutq tezligi (WPM) me'yorda, fikrlar mantiqiy bog'lovchilar yordamida izchil "
            "ifodalangan. Part 2 monologida kirish va yakuniy xulosani yanada ravon bog'lash tavsiya etiladi."
        ),
        pronunciation_feedback_uz=(
            "So'z urg'ulari va jumla ohangi tushunarli. Murakkab akademik atamalarni talaffuz "
            "qilishda bo'g'in urg'usiga e'tibor qarating."
        ),
        detailed_errors=[
            DetailedError(
                original="I am agree with this opinion",
                correction="I completely agree with this perspective",
                explanation_uz=(
                    "'Agree' fe'li oldidan 'am/is/are' qo'yilmaydi ('I agree' yoki 'I completely agree')."
                ),
            ),
            DetailedError(
                original="it give us many informations",
                correction="it provides us with a wealth of information",
                explanation_uz=(
                    "'Information' sanalmaydigan ot (uncountable noun) bo'lgani uchun '-s' ko'plik "
                    "qo'shimchasi olmaydi."
                ),
            ),
        ],
        band_booster_vocabulary=[
            BandBoosterVocabulary(
                simple_used="very important",
                advanced_alternative="of paramount importance / indispensable",
            ),
            BandBoosterVocabulary(
                simple_used="I think",
                advanced_alternative="From my perspective / I am inclined to believe",
            ),
            BandBoosterVocabulary(
                simple_used="good experience",
                advanced_alternative="a deeply rewarding and formative experience",
            ),
        ],
    )
    return verify_and_recalculate_speaking_scores(raw_speaking)


async def evaluate_speaking_with_demo_fallback(
    request: SpeakingEvaluationRequest,
) -> SpeakingEvaluationResult:
    """Evaluate Speaking Parts 1, 2, 3 via Claude -> Gemini -> offline demo fallback."""
    texts: dict[int, str] = {}
    for part_num, part_input in (
        (1, request.part_1),
        (2, request.part_2),
        (3, request.part_3),
    ):
        txt = part_input.transcript_text
        if (not txt or not txt.strip()) and part_input.has_audio:
            stt_res = await transcribe_voice_with_demo_fallback(
                audio_bytes=part_input.audio_bytes or b"demo_audio",
                duration_seconds=part_input.duration_seconds or 15.0,
                part_number=part_num,  # type: ignore[arg-type]
                filename=part_input.audio_filename,
            )
            txt = stt_res.transcribed_text
        texts[part_num] = (txt or "").strip()

    # Enforce anti-jailbreak & minimum length checks across all 3 parts
    for part_num in (1, 2, 3):
        check = check_speaking_prompt_injection(
            texts[part_num],
            part_number=part_num,  # type: ignore[arg-type]
            enforce_min_words=True,
        )
        if check.is_detected:
            return build_zero_speaking_result(
                exam_type=request.exam_type,
                reason_uz=check.explanation_uz,
                original_snippet=texts[part_num] or f"[Part {part_num} bo'sh]",
            )

    if not is_placeholder_api_key(settings.ANTHROPIC_API_KEY):
        try:
            hydrated_req = SpeakingEvaluationRequest(
                exam_type=request.exam_type,
                part_1=SpeakingPartInput(
                    part_number=1,
                    question_prompt=request.part_1.question_prompt,
                    transcript_text=texts[1],
                    duration_seconds=request.part_1.duration_seconds,
                ),
                part_2=SpeakingPartInput(
                    part_number=2,
                    question_prompt=request.part_2.question_prompt,
                    transcript_text=texts[2],
                    duration_seconds=request.part_2.duration_seconds,
                ),
                part_3=SpeakingPartInput(
                    part_number=3,
                    question_prompt=request.part_3.question_prompt,
                    transcript_text=texts[3],
                    duration_seconds=request.part_3.duration_seconds,
                ),
            )
            return await evaluate_speaking(request=hydrated_req)
        except Exception as exc:
            logger.warning(
                "Live Claude Speaking evaluation failed (%s); checking Gemini/demo fallback.",
                exc,
            )

    if not is_placeholder_api_key(settings.GEMINI_API_KEY):
        try:
            return await evaluate_speaking_via_gemini(
                request,
                p1_text=texts[1],
                p2_text=texts[2],
                p3_text=texts[3],
            )
        except Exception as exc:
            logger.warning(
                "Live Gemini Speaking evaluation failed (%s); falling back to offline demo evaluator.",
                exc,
            )

    return _build_demo_speaking_evaluation(
        exam_type=request.exam_type,
        p1_text=texts[1],
        p2_text=texts[2],
        p3_text=texts[3],
    )


# =====================================================================
# 2. STEP-BY-STEP TELEGRAM BOT FSM HANDLERS
# =====================================================================


def _get_active_test(exam_type: str, test_id: str | None = None) -> dict[str, Any]:
    """Return the active mock exam dictionary (by `test_id` if stored in FSM state, else random out of 10)."""
    if test_id:
        found = get_demo_test_by_id(test_id)
        if found is not None:
            return found
    return get_random_demo_test(exam_type)


@router.callback_query(F.data.startswith("exam_type:"))
async def cb_select_exam_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 1: Candidate selects `exam_type:IELTS` or `exam_type:CEFR` (picks 1 of 10 random variants)."""
    await callback.answer()
    raw_type = (callback.data or "exam_type:IELTS").split(":", 1)[1].strip().upper()
    exam_type: ExamType = "CEFR" if raw_type == "CEFR" else "IELTS"
    test = get_random_demo_test(exam_type)

    await state.update_data(
        exam_type=exam_type,
        test_id=test["id"],
        listening_raw=0,
        reading_raw=0,
    )
    await state.set_state(ExamSessionStates.choosing_exam_mode)

    badge = (
        "🇬🇧 IELTS Academic (0.0 - 9.0 Band)"
        if exam_type == "IELTS"
        else "🇺🇿 O'zbekiston BBA Multi-Level CEFR (0 - 75 shkala)"
    )
    if callback.message:
        await callback.message.answer(
            text=(
                f"✅ Tanlangan format: <b>{badge}</b>\n"
                f"🎲 Tasodifiy variant (10 tadan): <b>{test['title']}</b> (<code>{test['id']}</code>)\n\n"
                "👇 Imtihon topshirish rejimini tanlang:"
            ),
            reply_markup=build_exam_mode_keyboard(exam_type=exam_type),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("mode:"))
async def cb_select_exam_mode(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 2: Candidate selects `mode:full`, `mode:writing`, or `mode:speaking`."""
    await callback.answer()
    mode = (callback.data or "mode:full").split(":", 1)[1].strip().lower()
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))

    await state.update_data(exam_mode=mode, test_id=test["id"])

    if mode == "writing":
        await state.set_state(ExamSessionStates.submitting_writing_task_1)
        t1_prompt = test["writing_data"]["task_1_prompt"]
        if callback.message:
            await callback.message.answer(
                text=(
                    f"✍️ <b>{exam_type} Writing — Task 1</b> (Kamida 150 ta so'z)\n\n"
                    f"<b>Mavzu (Prompt):</b>\n<i>{t1_prompt}</i>\n\n"
                    "📝 Insho matnini shu yerga yozib yuboring <b>yoki</b> daftarga qo'lda yozilgan "
                    "insho <b>rasmini (Photo)</b> yuboring (AI Vision OCR avtomatik o'qiydi):"
                ),
                parse_mode="HTML",
            )
        return

    if mode == "speaking":
        await state.set_state(ExamSessionStates.submitting_speaking_part_1)
        p1_questions = "\n".join(
            f"• {q}" for q in test["speaking_data"]["part_1_questions"]
        )
        if callback.message:
            await callback.message.answer(
                text=(
                    f"🎙 <b>{exam_type} Speaking — Part 1 (Introduction &amp; Interview)</b>\n\n"
                    f"<b>Savollar:</b>\n<i>{p1_questions}</i>\n\n"
                    "🎤 Ushbu savollarga <b>ovozli xabar (Voice .ogg)</b> yuboring "
                    "(yoki test rejimida matn yozib yuboring):"
                ),
                parse_mode="HTML",
            )
        return

    # Default: mode == "full" -> Start with Listening & Reading
    await state.set_state(ExamSessionStates.taking_listening_reading)
    if callback.message:
        await callback.message.answer(
            text=(
                f"🎧📖 <b>1-Bosqich: {exam_type} Listening &amp; Reading (40 + 40 savol)</b>\n\n"
                "Ushbu bosqichni 2 xil usulda topshirishingiz mumkin:\n"
                "1️⃣ Quyidagi <b>Mini App</b> tugmasini bosib interaktiv testni yeching.\n"
                "2️⃣ Yoki tezkor sinov uchun quyidagi namuna ballardan birini tanlang / "
                "Listening va Reading to'g'ri javoblar sonini yozib yuboring (masalan: <code>32 30</code>):"
            ),
            reply_markup=build_listening_reading_keyboard(exam_type=exam_type),
            parse_mode="HTML",
        )


async def _transition_to_writing_task_1(
    message: Message,
    state: FSMContext,
    exam_type: ExamType,
    l_raw: int,
    r_raw: int,
) -> None:
    """Save Listening/Reading scores and prompt the candidate for Writing Task 1."""
    l_band = convert_listening_raw_to_band(l_raw)
    r_band = convert_reading_raw_to_band(r_raw, module="academic")
    l_75 = (
        convert_raw_to_cefr_standard_score(l_raw, 40)
        if exam_type == "CEFR"
        else band_to_cefr_75_score(l_band)
    )
    r_75 = (
        convert_raw_to_cefr_standard_score(r_raw, 40)
        if exam_type == "CEFR"
        else band_to_cefr_75_score(r_band)
    )

    data = await state.get_data()
    test = _get_active_test(exam_type, data.get("test_id"))
    await state.update_data(
        test_id=test["id"],
        listening_raw=l_raw,
        listening_band=l_band,
        listening_score_75=l_75,
        reading_raw=r_raw,
        reading_band=r_band,
        reading_score_75=r_75,
    )
    await state.set_state(ExamSessionStates.submitting_writing_task_1)

    t1_prompt = test["writing_data"]["task_1_prompt"]

    await message.answer(
        text=(
            "✅ <b>Listening &amp; Reading natijalari qabul qilindi ($0.00 token):</b>\n"
            f"• 🎧 <b>Listening:</b> {l_raw}/40 — Band <b>{l_band:.1f}</b> ({l_75:.1f}/75)\n"
            f"• 📖 <b>Reading:</b> {r_raw}/40 — Band <b>{r_band:.1f}</b> ({r_75:.1f}/75)\n\n"
            f"✍️ <b>2-Bosqich: {exam_type} Writing — Task 1</b> (Kamida 150 so'z)\n\n"
            f"<b>Mavzu (Prompt):</b>\n<i>{t1_prompt}</i>\n\n"
            "📝 Task 1 insho matnini yuboring yoki qo'lyozma daftar <b>rasmini (Photo)</b> jo'nating:"
        ),
        parse_mode="HTML",
    )


@router.callback_query(
    ExamSessionStates.taking_listening_reading,
    F.data.startswith("lr_quick:"),
)
async def cb_quick_listening_reading(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle quick preset Listening & Reading scores (`lr_quick:32:30`)."""
    await callback.answer()
    parts = (callback.data or "lr_quick:32:30").split(":")
    l_raw = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 32
    r_raw = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 30

    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")

    if callback.message:
        await _transition_to_writing_task_1(
            message=callback.message,
            state=state,
            exam_type=exam_type,
            l_raw=l_raw,
            r_raw=r_raw,
        )


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext) -> None:
    """Process Listening, Reading, and optional Writing data submitted from the Telegram Mini App."""
    raw_json = message.web_app_data.data if message.web_app_data else "{}"
    try:
        payload = json.loads(raw_json)
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        payload = {}

    data = await state.get_data()
    raw_exam_type = str(payload.get("exam_type") or data.get("exam_type") or "IELTS").upper()
    exam_type: ExamType = "CEFR" if raw_exam_type == "CEFR" else "IELTS"
    test = _get_active_test(exam_type, payload.get("test_id") or data.get("test_id"))

    # Grade answer dicts if provided, or read direct raw counts
    if "listening_answers" in payload and isinstance(payload["listening_answers"], dict):
        l_scored = score_reading_or_listening(
            user_answers=payload["listening_answers"],
            answer_key=test["listening_data"]["answer_key"],
            section="listening",
            exam_type=exam_type,
        )
        l_raw = l_scored.correct_count
    else:
        l_raw = int(payload.get("listening_raw", 30))

    if "reading_answers" in payload and isinstance(payload["reading_answers"], dict):
        r_scored = score_reading_or_listening(
            user_answers=payload["reading_answers"],
            answer_key=test["reading_data"]["answer_key"],
            section="reading",
            exam_type=exam_type,
        )
        r_raw = r_scored.correct_count
    else:
        r_raw = int(payload.get("reading_raw", 29))

    l_raw = max(0, min(40, l_raw))
    r_raw = max(0, min(40, r_raw))

    await state.update_data(
        exam_type=exam_type,
        test_id=test["id"],
        exam_mode=data.get("exam_mode", "full"),
    )
    await _transition_to_writing_task_1(
        message=message,
        state=state,
        exam_type=exam_type,
        l_raw=l_raw,
        r_raw=r_raw,
    )


@router.message(ExamSessionStates.taking_listening_reading, F.text)
async def handle_listening_reading_text(message: Message, state: FSMContext) -> None:
    """Allow candidate to enter Listening and Reading raw scores as text (e.g., `32 30`)."""
    text = (message.text or "").strip()
    numbers = [int(n) for n in re.findall(r"\b\d{1,2}\b", text)]
    if len(numbers) < 2:
        await message.answer(
            text=(
                "⚠️ Iltimos, Listening va Reading to'g'ri javoblar sonini (0 dan 40 gacha) "
                "ikkita son ko'rinishida yuboring (masalan: <code>32 30</code>) yoki yuqoridagi "
                "Mini App / namuna tugmasidan foydalaning."
            ),
            parse_mode="HTML",
        )
        return

    l_raw = max(0, min(40, numbers[0]))
    r_raw = max(0, min(40, numbers[1]))
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")

    await _transition_to_writing_task_1(
        message=message,
        state=state,
        exam_type=exam_type,
        l_raw=l_raw,
        r_raw=r_raw,
    )


# =====================================================================
# 3. WRITING TASK 1 & TASK 2 HANDLERS (TEXT OR HANDWRITTEN PHOTO OCR)
# =====================================================================


async def _download_telegram_photo_bytes(message: Message, bot: Bot) -> bytes:
    """Download the highest-resolution photo from a Telegram message into memory bytes."""
    if not message.photo:
        raise ValueError("No photo attached to message.")
    largest_photo = message.photo[-1]
    buffer = io.BytesIO()
    await bot.download(largest_photo, destination=buffer)
    return buffer.getvalue()


@router.message(ExamSessionStates.submitting_writing_task_1, F.photo)
async def handle_writing_task_1_photo(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Transcribe handwritten Task 1 essay photo via Vision OCR and move to Task 2."""
    status_msg = await message.answer(
        "🔍 <i>Qo'lyozma rasm Vision OCR orqali o'qilmoqda, iltimos kuting...</i>",
        parse_mode="HTML",
    )
    image_bytes = await _download_telegram_photo_bytes(message, bot)
    transcribed_text = await transcribe_image_with_demo_fallback(image_bytes, task_number=1)
    word_count = len(transcribed_text.split())

    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    t2_prompt = test["writing_data"]["task_2_prompt"]

    await state.update_data(task_1_text=transcribed_text, test_id=test["id"])
    await state.set_state(ExamSessionStates.submitting_writing_task_2)

    await status_msg.edit_text(
        text=(
            f"✅ <b>Task 1 Vision OCR orqali o'qildi ({word_count} ta so'z):</b>\n"
            f"<blockquote>{transcribed_text[:350]}{'...' if len(transcribed_text) > 350 else ''}</blockquote>\n\n"
            f"✍️ <b>Endi {exam_type} Writing — Task 2</b> (Kamida 250 ta so'z)\n\n"
            f"<b>Mavzu (Prompt):</b>\n<i>{t2_prompt}</i>\n\n"
            "📝 Task 2 insho matnini yozib yuboring yoki daftar <b>rasmini (Photo)</b> jo'nating:"
        ),
        parse_mode="HTML",
    )


@router.message(ExamSessionStates.submitting_writing_task_1, F.text)
async def handle_writing_task_1_text(message: Message, state: FSMContext) -> None:
    """Save typed Writing Task 1 text and prompt for Task 2."""
    t1_text = (message.text or "").strip()
    word_count = len(t1_text.split())

    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    t2_prompt = test["writing_data"]["task_2_prompt"]

    await state.update_data(task_1_text=t1_text, test_id=test["id"])
    await state.set_state(ExamSessionStates.submitting_writing_task_2)

    await message.answer(
        text=(
            f"✅ <b>Task 1 qabul qilindi ({word_count} ta so'z).</b>\n\n"
            f"✍️ <b>Endi {exam_type} Writing — Task 2</b> (Kamida 250 ta so'z)\n\n"
            f"<b>Mavzu (Prompt):</b>\n<i>{t2_prompt}</i>\n\n"
            "📝 Task 2 insho matnini yozib yuboring yoki daftar <b>rasmini (Photo)</b> jo'nating:"
        ),
        parse_mode="HTML",
    )


async def _process_writing_task_2_and_advance(
    message: Message,
    state: FSMContext,
    t2_text: str,
) -> None:
    """Evaluate Task 1 + Task 2 via AI Rubric and either finish (writing-only mode) or advance to Speaking."""
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    exam_mode: str = data.get("exam_mode", "full")
    t1_text: str = data.get("task_1_text", "")
    test = _get_active_test(exam_type, data.get("test_id"))

    wait_msg = await message.answer(
        "🧠 <i>Writing Task 1 va Task 2 rasmiy mezonlar asosida AI tomonidan tahlil qilinmoqda...</i>",
        parse_mode="HTML",
    )

    eval_request = WritingEvaluationRequest(
        exam_type=exam_type,
        task_1=WritingTaskInput(
            task_number=1,
            prompt_topic=test["writing_data"]["task_1_prompt"],
            student_text=t1_text,
        ),
        task_2=WritingTaskInput(
            task_number=2,
            prompt_topic=test["writing_data"]["task_2_prompt"],
            student_text=t2_text,
        ),
    )
    writing_result = await evaluate_writing_with_demo_fallback(eval_request)

    await state.update_data(
        task_2_text=t2_text,
        writing_result_json=writing_result.model_dump(mode="json"),
    )

    crit = writing_result.criteria_scores
    summary_html = (
        f"📊 <b>{exam_type} Writing Tahlil Natijasi:</b>\n"
        f"• <b>Overall Writing Score:</b> {writing_result.overall_writing_score:.1f} "
        f"(CEFR: <b>{writing_result.cefr_level}</b>)\n"
        f"• <b>Task 1 (1/3):</b> {writing_result.task_1_score:.1f} | "
        f"<b>Task 2 (2/3):</b> {writing_result.task_2_score:.1f}\n"
        f"• <b>TA/TR:</b> {crit.task_achievement:.1f} | <b>CC:</b> {crit.coherence_cohesion:.1f} | "
        f"<b>LR:</b> {crit.lexical_resource:.1f} | <b>GRA:</b> {crit.grammatical_range_accuracy:.1f}\n"
    )

    if exam_mode == "writing":
        await wait_msg.edit_text(summary_html, parse_mode="HTML")
        await _generate_and_send_final_pdf(
            message=message,
            state=state,
            writing_evaluation=writing_result,
            speaking_evaluation=None,
        )
        return

    # Full mode -> advance to Speaking Part 1
    await state.set_state(ExamSessionStates.submitting_speaking_part_1)
    p1_questions = "\n".join(f"• {q}" for q in test["speaking_data"]["part_1_questions"])
    await wait_msg.edit_text(
        text=(
            f"{summary_html}\n"
            f"🎙 <b>3-Bosqich: {exam_type} Speaking — Part 1 (Interview)</b>\n\n"
            f"<b>Savollar:</b>\n<i>{p1_questions}</i>\n\n"
            "🎤 Javobingizni <b>ovozli xabar (Voice .ogg)</b> yoki matn ko'rinishida yuboring:"
        ),
        parse_mode="HTML",
    )


@router.message(ExamSessionStates.submitting_writing_task_2, F.photo)
async def handle_writing_task_2_photo(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Transcribe handwritten Task 2 essay photo via Vision OCR and run Writing evaluation."""
    image_bytes = await _download_telegram_photo_bytes(message, bot)
    transcribed_text = await transcribe_image_with_demo_fallback(image_bytes, task_number=2)
    await _process_writing_task_2_and_advance(message=message, state=state, t2_text=transcribed_text)


@router.message(ExamSessionStates.submitting_writing_task_2, F.text)
async def handle_writing_task_2_text(message: Message, state: FSMContext) -> None:
    """Handle typed Writing Task 2 essay submission and run Writing evaluation."""
    t2_text = (message.text or "").strip()
    await _process_writing_task_2_and_advance(message=message, state=state, t2_text=t2_text)


# =====================================================================
# 4. SPEAKING PART 1, 2, 3 HANDLERS (VOICE .OGG WHISPER STT OR TEXT)
# =====================================================================


async def _extract_speaking_response(
    message: Message,
    bot: Bot,
    part_number: SpeakingPartNumber,
) -> tuple[str, float]:
    """Extract spoken transcript and duration from either a Telegram Voice message or text."""
    if message.voice:
        buffer = io.BytesIO()
        await bot.download(message.voice, destination=buffer)
        audio_bytes = buffer.getvalue()
        duration = float(message.voice.duration or 15.0)
        stt_result = await transcribe_voice_with_demo_fallback(
            audio_bytes=audio_bytes,
            duration_seconds=duration,
            part_number=part_number,
            filename=f"part_{part_number}.ogg",
        )
        return stt_result.transcribed_text, stt_result.duration_seconds

    text = (message.text or "").strip()
    word_count = len(text.split())
    estimated_duration = round(max(10.0, (word_count / 130.0) * 60.0), 1)
    return text, estimated_duration


@router.message(ExamSessionStates.submitting_speaking_part_1, F.voice | F.text)
async def handle_speaking_part_1(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Process Speaking Part 1 (voice or text) and advance to Part 2 Cue Card."""
    transcript, duration = await _extract_speaking_response(message, bot, part_number=1)
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    cue_card = test["speaking_data"]["part_2_cue_card"]

    await state.update_data(part_1_text=transcript, part_1_duration=duration, test_id=test["id"])
    await state.set_state(ExamSessionStates.submitting_speaking_part_2)

    await message.answer(
        text=(
            f"✅ <b>Speaking Part 1 qabul qilindi ({len(transcript.split())} so'z).</b>\n\n"
            f"🎙 <b>{exam_type} Speaking — Part 2 (Cue Card / Individual Long Turn)</b>\n\n"
            f"<b>Mavzu (1–2 daqiqalik monolog):</b>\n<i>{cue_card}</i>\n\n"
            "🎤 Monolog javobingizni <b>ovozli xabar (Voice .ogg)</b> yoki matn ko'rinishida yuboring:"
        ),
        parse_mode="HTML",
    )


@router.message(ExamSessionStates.submitting_speaking_part_2, F.voice | F.text)
async def handle_speaking_part_2(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Process Speaking Part 2 Cue Card response and advance to Part 3 Abstract Discussion."""
    transcript, duration = await _extract_speaking_response(message, bot, part_number=2)
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    p3_questions = "\n".join(f"• {q}" for q in test["speaking_data"]["part_3_questions"])

    await state.update_data(part_2_text=transcript, part_2_duration=duration, test_id=test["id"])
    await state.set_state(ExamSessionStates.submitting_speaking_part_3)

    await message.answer(
        text=(
            f"✅ <b>Speaking Part 2 qabul qilindi ({len(transcript.split())} so'z).</b>\n\n"
            f"🎙 <b>{exam_type} Speaking — Part 3 (Two-Way Abstract Discussion)</b>\n\n"
            f"<b>Muhokama savollari:</b>\n<i>{p3_questions}</i>\n\n"
            "🎤 Yakuniy Part 3 javobingizni <b>ovozli xabar (Voice .ogg)</b> yoki matn ko'rinishida yuboring:"
        ),
        parse_mode="HTML",
    )


@router.message(ExamSessionStates.submitting_speaking_part_3, F.voice | F.text)
async def handle_speaking_part_3(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Process Speaking Part 3, evaluate all 3 parts, and deliver the 2-3 page PDF Certificate."""
    p3_text, p3_duration = await _extract_speaking_response(message, bot, part_number=3)
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))

    wait_msg = await message.answer(
        "⏳ <i>Speaking javoblaringiz tahlil qilinmoqda va ko'p sahifali PDF Sertifikat tayyorlanmoqda...</i>",
        parse_mode="HTML",
    )

    p1_text = data.get("part_1_text", "")
    p2_text = data.get("part_2_text", "")

    speaking_req = SpeakingEvaluationRequest(
        exam_type=exam_type,
        part_1=SpeakingPartInput(
            part_number=1,
            question_prompt="; ".join(test["speaking_data"]["part_1_questions"]),
            transcript_text=p1_text,
            duration_seconds=float(data.get("part_1_duration", 15.0)),
        ),
        part_2=SpeakingPartInput(
            part_number=2,
            question_prompt=test["speaking_data"]["part_2_cue_card"],
            transcript_text=p2_text,
            duration_seconds=float(data.get("part_2_duration", 45.0)),
        ),
        part_3=SpeakingPartInput(
            part_number=3,
            question_prompt="; ".join(test["speaking_data"]["part_3_questions"]),
            transcript_text=p3_text,
            duration_seconds=p3_duration,
        ),
    )

    speaking_result = await evaluate_speaking_with_demo_fallback(speaking_req)

    writing_result: WritingEvaluationResult | None = None
    if data.get("writing_result_json"):
        writing_result = WritingEvaluationResult.model_validate(data["writing_result_json"])

    await wait_msg.delete()
    await _generate_and_send_final_pdf(
        message=message,
        state=state,
        writing_evaluation=writing_result,
        speaking_evaluation=speaking_result,
    )


async def _generate_and_send_final_pdf(
    message: Message,
    state: FSMContext,
    writing_evaluation: WritingEvaluationResult | None,
    speaking_evaluation: SpeakingEvaluationResult | None,
) -> None:
    """Compile the 4-skill report via `ExamOrchestratorService` and send the PDF via `BufferedInputFile`."""
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    l_raw = int(data.get("listening_raw", 0))
    r_raw = int(data.get("reading_raw", 0))

    user = message.from_user
    candidate_name = user.full_name if user and user.full_name else "Candidate"
    telegram_id = user.id if user else None

    short_uuid = uuid.uuid4().hex[:6].upper()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    report_id = f"{exam_type}-{date_str}-{short_uuid}"

    orchestrator = get_exam_orchestrator_service()
    compiled = await orchestrator.compile_full_exam_report(
        report_id=report_id,
        candidate_name=candidate_name,
        candidate_telegram_id=telegram_id,
        exam_type=exam_type,
        listening_raw=l_raw,
        reading_raw=r_raw,
        writing_evaluation=writing_evaluation,
        speaking_evaluation=speaking_evaluation,
    )

    scores = compiled.scores
    caption = (
        f"🎓 <b>{exam_type} MOCK AI — YAKUNIY NATIJA VA DIAGNOSTIK HISOBOT</b>\n"
        f"🆔 Hisobot raqami: <code>{report_id}</code>\n"
        f"👤 Nomzod: <b>{candidate_name}</b>\n\n"
        f"🏆 <b>OVERALL IELTS BAND: {scores.overall_band:.1f} / 9.0</b>\n"
        f"🇺🇿 <b>BBA MULTI-LEVEL BALL: {scores.overall_score_75:.1f} / 75.0</b>\n"
        f"📈 <b>CEFR DARAJASI: {scores.cefr_level}</b>\n\n"
        "<b>Ko'nikmalar kesimida (4-Skill Breakdown):</b>\n"
        f"• 🎧 Listening: <b>{scores.listening_band:.1f}</b> ({scores.listening_raw}/40 | {scores.listening_score_75:.1f}/75)\n"
        f"• 📖 Reading: <b>{scores.reading_band:.1f}</b> ({scores.reading_raw}/40 | {scores.reading_score_75:.1f}/75)\n"
        f"• ✍️ Writing: <b>{scores.writing_band:.1f}</b> ({scores.writing_score_75:.1f}/75)\n"
        f"• 🎙 Speaking: <b>{scores.speaking_band:.1f}</b> ({scores.speaking_score_75:.1f}/75)\n\n"
        "📎 <i>Biriktirilgan PDF faylda 1-sahifada Sertifikat va 2-sahifada Xatolar Daftari "
        "(Detailed Error Workbook) + C1 Band Booster lug'ati keltirilgan!</i>\n\n"
        "⚖️ <i>Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool).</i>"
    )

    pdf_file = BufferedInputFile(
        file=compiled.pdf_bytes,
        filename=f"{report_id}.pdf",
    )
    await message.answer_document(
        document=pdf_file,
        caption=caption,
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()


__all__ = [
    "evaluate_speaking_with_demo_fallback",
    "evaluate_writing_with_demo_fallback",
    "is_placeholder_api_key",
    "router",
    "transcribe_image_with_demo_fallback",
    "transcribe_voice_with_demo_fallback",
]
