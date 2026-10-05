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

import base64
import binascii
import html
import io
import logging
from typing import Any, Literal

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import ExceptionTypeFilter, StateFilter
from aiogram.types import BufferedInputFile, CallbackQuery, ErrorEvent, Message

from app.bot.keyboards.exam_kb import build_exam_mode_keyboard, build_main_menu_keyboard
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
from app.services import usage_limits
from app.services.chart_renderer import render_task1_chart
from app.services.gemini_evaluator import (
    evaluate_speaking_via_gemini,
    evaluate_writing_via_gemini,
    transcribe_audio_via_gemini,
    transcribe_handwritten_image_via_gemini,
)
from app.services.reading_listening_scorer import round_to_half_band
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


class AIServiceUnavailableError(RuntimeError):
    """Raised when no AI provider could process a submission and demo fallback is disabled."""


def _ensure_demo_fallback_allowed(what: str) -> None:
    """Refuse to substitute canned demo output unless `ALLOW_DEMO_AI_FALLBACK` is enabled."""
    if not settings.ALLOW_DEMO_AI_FALLBACK:
        raise AIServiceUnavailableError(f"{what} is temporarily unavailable (all AI providers failed).")


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

    _ensure_demo_fallback_allowed("Handwriting OCR")
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

    _ensure_demo_fallback_allowed("Speech-to-text")
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


def _resolve_task_image_bytes(task: WritingTaskInput) -> bytes:
    """Return raw image bytes for OCR from `image_bytes` or a (data-URL or plain) `image_base64` string."""
    if task.image_bytes:
        return task.image_bytes
    if task.image_base64:
        payload = task.image_base64.split(",", 1)[-1] if task.image_base64.startswith("data:") else task.image_base64
        try:
            return base64.b64decode(payload, validate=False)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"Task {task.task_number} image is not valid base64.") from exc
    return b""


async def evaluate_writing_with_demo_fallback(
    request: WritingEvaluationRequest,
    feedback_language: str = "uz",
) -> WritingEvaluationResult:
    """Evaluate Writing Task 1 & Task 2 via Claude -> Gemini -> offline demo fallback."""
    t1_text = request.task_1.student_text
    if (not t1_text or not t1_text.strip()) and request.task_1.has_image:
        t1_text = await transcribe_image_with_demo_fallback(
            _resolve_task_image_bytes(request.task_1),
            task_number=1,
        )

    t2_text = request.task_2.student_text
    if (not t2_text or not t2_text.strip()) and request.task_2.has_image:
        t2_text = await transcribe_image_with_demo_fallback(
            _resolve_task_image_bytes(request.task_2),
            task_number=2,
        )

    # Layer 1: cheating / prompt injection / gibberish zeroes the whole paper. A short or missing
    # task does NOT: the AI still marks the other task, and a missing task simply scores 0.
    missing: set[int] = set()
    for num, text in ((1, t1_text), (2, t2_text)):
        if not text or not text.strip():
            missing.add(num)
            continue
        check = check_prompt_injection(text, task_number=num, enforce_min_words=False)  # type: ignore[arg-type]
        if check.is_detected:
            return build_zero_score_result(
                exam_type=request.exam_type,
                reason_uz=check.explanation_uz,
                original_snippet=text,
            )
    if missing == {1, 2}:
        return build_zero_score_result(
            exam_type=request.exam_type,
            reason_uz="Hech bir task uchun javob yuborilmadi. / No answer was submitted for either task.",
            original_snippet="[Task 1 va Task 2 bo'sh]",
        )
    t1_text = t1_text if 1 not in missing else NO_RESPONSE_PLACEHOLDER
    t2_text = t2_text if 2 not in missing else NO_RESPONSE_PLACEHOLDER
    result = await _evaluate_writing_texts(request, t1_text, t2_text, feedback_language)
    if missing:
        result = verify_and_recalculate_scores(result.model_copy(update={
            "task_1_score": 0.0 if 1 in missing else result.task_1_score,
            "task_2_score": 0.0 if 2 in missing else result.task_2_score,
        }))
    return result


NO_RESPONSE_PLACEHOLDER = "[The candidate did not submit an answer for this task.]"


async def _evaluate_writing_texts(
    request: WritingEvaluationRequest,
    t1_text: str,
    t2_text: str,
    feedback_language: str,
) -> WritingEvaluationResult:
    """Claude -> Gemini -> (optional) demo fallback for already screened texts."""

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
                feedback_language=feedback_language,
            )
        except Exception as exc:
            logger.warning(
                "Live Gemini Writing evaluation failed (%s); falling back to offline demo evaluator.",
                exc,
            )

    _ensure_demo_fallback_allowed("Writing evaluation")
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
    feedback_language: str = "uz",
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

    # Cheating / injection / gibberish zeroes everything; a short or missing part does not —
    # the examiner marks what was said (a missing part is shown to the AI as "no response").
    answered = [p for p in (1, 2, 3) if texts[p]]
    for part_num in answered:
        check = check_speaking_prompt_injection(
            texts[part_num],
            part_number=part_num,  # type: ignore[arg-type]
            enforce_min_words=False,
        )
        if check.is_detected:
            return build_zero_speaking_result(
                exam_type=request.exam_type,
                reason_uz=check.explanation_uz,
                original_snippet=texts[part_num],
            )
    if not answered:
        return build_zero_speaking_result(
            exam_type=request.exam_type,
            reason_uz="Hech bir savolga javob qayd etilmadi (mikrofonni tekshiring). / No spoken answers were recorded — please check your microphone.",
            original_snippet="[Part 1-3 bo'sh]",
        )
    for part_num in (1, 2, 3):
        if not texts[part_num]:
            texts[part_num] = NO_RESPONSE_PLACEHOLDER.replace("task", "part")

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
                feedback_language=feedback_language,
            )
        except Exception as exc:
            logger.warning(
                "Live Gemini Speaking evaluation failed (%s); falling back to offline demo evaluator.",
                exc,
            )

    _ensure_demo_fallback_allowed("Speaking evaluation")
    return _build_demo_speaking_evaluation(
        exam_type=request.exam_type,
        p1_text=texts[1],
        p2_text=texts[2],
        p3_text=texts[3],
    )


# =====================================================================
# 2. TELEGRAM PRACTICE FLOW (Writing & Speaking in chat; full mock in the Mini App)
# =====================================================================


def _get_active_test(exam_type: str, test_id: str | None = None) -> dict[str, Any]:
    """Return the mock exam stored in FSM state, else a random variant."""
    if test_id:
        found = get_demo_test_by_id(test_id)
        if found is not None:
            return found
    return get_random_demo_test(exam_type)


def _feedback_language(user: Any) -> str:
    code = (getattr(user, "language_code", None) or "").lower()
    return "ru" if code.startswith("ru") else ("en" if code.startswith("en") else "uz")


def _subjects(user_id: int) -> list[str]:
    return [f"tg:{user_id}"]


async def _quota_left(user_id: int) -> int:
    decision = await usage_limits.remaining(usage_limits.EXAM, _subjects(user_id))
    return decision.remaining


LIMIT_REACHED_TEXT = (
    "⏳ <b>Daily limit reached.</b> You can take {limit} AI-scored exams per day — come back tomorrow!\n"
    "Kunlik limit tugadi: kuniga {limit} ta AI baholaydigan imtihon. Ertaga qayta urinib ko'ring.\n\n"
    "🎧📖 Listening &amp; Reading practice in the Mini App is unlimited."
)


@router.callback_query(F.data.startswith("exam_type:"))
async def cb_select_exam_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 1: IELTS or CEFR (a random variant is picked)."""
    await callback.answer()
    raw_type = (callback.data or "exam_type:IELTS").split(":", 1)[1].strip().upper()
    exam_type: ExamType = "CEFR" if raw_type == "CEFR" else "IELTS"
    test = get_random_demo_test(exam_type)
    await state.update_data(exam_type=exam_type, test_id=test["id"])
    await state.set_state(ExamSessionStates.choosing_exam_mode)
    if callback.message:
        await callback.message.answer(
            text=(
                f"✅ <b>{'IELTS Academic' if exam_type == 'IELTS' else 'Multilevel CEFR'}</b> — {test['title']}\n\n"
                "Choose what you want to practise:\n"
                "• <b>Full mock</b> — all 4 skills in the Mini App, with a PDF report\n"
                "• <b>Writing</b> or <b>Speaking</b> — right here in the chat"
            ),
            reply_markup=build_exam_mode_keyboard(exam_type=exam_type),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("mode:"))
async def cb_select_exam_mode(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 2: writing or speaking practice in chat (the full mock lives in the Mini App)."""
    await callback.answer()
    mode = (callback.data or "mode:writing").split(":", 1)[1].strip().lower()
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    message = callback.message
    if message is None or callback.from_user is None:
        return

    left = await _quota_left(callback.from_user.id)
    if left <= 0:
        await message.answer(LIMIT_REACHED_TEXT.format(limit=settings.DAILY_EXAM_LIMIT), parse_mode="HTML")
        return

    await state.update_data(exam_mode=mode, test_id=test["id"])
    if mode == "speaking":
        await _start_speaking(message, state, test)
        return
    await _start_writing(message, state, test)


# ----------------------------- Writing --------------------------------


async def _start_writing(message: Message, state: FSMContext, test: dict[str, Any]) -> None:
    await state.set_state(ExamSessionStates.submitting_writing_task_1)
    writing = test["writing_data"]
    header = (
        "✍️ <b>WRITING TASK 1</b> — spend about 20 minutes. Write at least 150 words.\n\n"
        f"<i>{writing['task_1_prompt']}</i>\n\n"
        "Send your answer as text, or a clear photo of your handwritten answer.\n"
        "<i>Javobni matn yoki qo'lyozma rasmi sifatida yuboring.</i>"
    )
    chart_png = render_task1_chart(test["id"])
    if chart_png:
        await message.answer_photo(
            photo=BufferedInputFile(chart_png, filename="task1.png"),
            caption="Writing Task 1 — visual",
        )
    await message.answer(header, parse_mode="HTML")


async def _download_telegram_photo_bytes(message: Message, bot: Bot) -> bytes:
    """Download the highest-resolution photo attached to a message."""
    if not message.photo:
        return b""
    file = await bot.get_file(message.photo[-1].file_id)
    buffer = io.BytesIO()
    await bot.download_file(file.file_path, destination=buffer)  # type: ignore[arg-type]
    return buffer.getvalue()


async def _writing_answer_text(message: Message, bot: Bot, task_number: Literal[1, 2]) -> str:
    if message.photo:
        await message.answer("🔍 Reading your handwriting… / Qo'lyozma o'qilmoqda…")
        image = await _download_telegram_photo_bytes(message, bot)
        return await transcribe_image_with_demo_fallback(image, task_number=task_number)
    return (message.text or "").strip()


@router.message(ExamSessionStates.submitting_writing_task_1, F.photo | F.text)
async def handle_writing_task_1(message: Message, state: FSMContext, bot: Bot) -> None:
    text = await _writing_answer_text(message, bot, 1)
    data = await state.get_data()
    test = _get_active_test(data.get("exam_type", "IELTS"), data.get("test_id"))
    await state.update_data(task_1_text=text)
    await state.set_state(ExamSessionStates.submitting_writing_task_2)
    await message.answer(
        f"✅ Task 1 received ({len(text.split())} words).\n\n"
        "✍️ <b>WRITING TASK 2</b> — spend about 40 minutes. Write at least 250 words.\n\n"
        f"<i>{test['writing_data']['task_2_prompt']}</i>",
        parse_mode="HTML",
    )


@router.message(ExamSessionStates.submitting_writing_task_2, F.photo | F.text)
async def handle_writing_task_2(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None:
        return
    t2_text = await _writing_answer_text(message, bot, 2)
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))

    decision = await usage_limits.consume(usage_limits.EXAM, _subjects(message.from_user.id))
    if not decision.allowed:
        await message.answer(LIMIT_REACHED_TEXT.format(limit=settings.DAILY_EXAM_LIMIT), parse_mode="HTML")
        return

    wait = await message.answer("⏳ The AI examiner is marking your essays… / Baholanmoqda…")
    task_1_prompt = test["writing_data"]["task_1_prompt"]
    if test["writing_data"].get("task_1_chart_text"):
        task_1_prompt += "\n\nDATA SHOWN IN THE VISUAL:\n" + test["writing_data"]["task_1_chart_text"]
    request = WritingEvaluationRequest(
        exam_type=exam_type,
        task_1=WritingTaskInput(task_number=1, prompt_topic=task_1_prompt, student_text=data.get("task_1_text", "")),
        task_2=WritingTaskInput(task_number=2, prompt_topic=test["writing_data"]["task_2_prompt"], student_text=t2_text),
    )
    try:
        result = await evaluate_writing_with_demo_fallback(request, feedback_language=_feedback_language(message.from_user))
    except AIServiceUnavailableError:
        await usage_limits.refund(usage_limits.EXAM, _subjects(message.from_user.id))
        raise
    finally:
        await wait.delete()

    await message.answer(_format_writing_result(result, exam_type), parse_mode="HTML", reply_markup=build_main_menu_keyboard())
    await state.clear()


def _band_or_75(value: float, exam_type: str) -> str:
    return f"{value:.1f}" if exam_type == "IELTS" else f"{band_to_cefr_75_score(value):.1f}/75"


def _format_errors_and_vocab(errors: list[Any], vocab: list[Any]) -> str:
    lines: list[str] = []
    if errors:
        lines.append("\n🔍 <b>Key mistakes</b>")
        for err in errors[:6]:
            lines.append(
                f"• <s>{html.escape(err.original)}</s> → <b>{html.escape(err.correction)}</b>\n"
                f"  <i>{html.escape(err.explanation_uz)}</i>"
            )
    if vocab:
        lines.append("\n🚀 <b>Vocabulary upgrades</b>")
        for v in vocab[:5]:
            lines.append(f"• {html.escape(v.simple_used)} → <b>{html.escape(v.advanced_alternative)}</b>")
    return "\n".join(lines)


def _format_writing_result(result: WritingEvaluationResult, exam_type: str) -> str:
    c = result.criteria_scores
    return (
        f"📊 <b>Writing result ({exam_type})</b>\n\n"
        f"Overall: <b>{_band_or_75(result.overall_writing_score, exam_type)}</b>  (CEFR {result.cefr_level})\n"
        f"Task 1: {result.task_1_score:.1f} • Task 2: {result.task_2_score:.1f}\n"
        f"Task Achievement/Response {c.task_achievement:.1f} • Coherence &amp; Cohesion {c.coherence_cohesion:.1f}\n"
        f"Lexical Resource {c.lexical_resource:.1f} • Grammar {c.grammatical_range_accuracy:.1f}"
        + (f"\n\n🧑‍🏫 {html.escape(result.examiner_summary)}" if result.examiner_summary else "")
        + _format_errors_and_vocab(result.detailed_errors, result.band_booster_vocabulary)
        + "\n\n<i>Unofficial AI mock assessment — not an official IELTS/CEFR result.</i>"
    )


# ----------------------------- Speaking -------------------------------


def _speaking_queue(test: dict[str, Any]) -> list[dict[str, Any]]:
    sd = test["speaking_data"]
    queue: list[dict[str, Any]] = []
    for topic in sd.get("part_1_topics") or [{"topic": "", "questions": sd["part_1_questions"]}]:
        for q in topic["questions"]:
            queue.append({"part": 1, "text": q})
    queue.append({"part": 2, "text": sd["part_2_cue_card"]})
    for q in sd["part_3_questions"]:
        queue.append({"part": 3, "text": q})
    return queue


async def _ask_speaking_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue, idx = data["speaking_queue"], data["speaking_index"]
    item = queue[idx]
    part_intro = {1: "🎙 <b>SPEAKING PART 1</b> — Interview", 2: "🎙 <b>SPEAKING PART 2</b> — Long turn", 3: "🎙 <b>SPEAKING PART 3</b> — Discussion"}
    first_of_part = idx == 0 or queue[idx - 1]["part"] != item["part"]
    prefix = part_intro[item["part"]] + "\n\n" if first_of_part else ""
    if item["part"] == 2:
        body = (
            f"<i>{html.escape(item['text'])}</i>\n\n"
            "You have <b>1 minute</b> to prepare, then speak for <b>1–2 minutes</b>.\n"
            "Send ONE voice message. / Bitta ovozli xabar yuboring."
        )
    else:
        number = sum(1 for q in queue[: idx + 1] if q["part"] == item["part"])
        body = f"<b>Q{number}.</b> {html.escape(item['text'])}\n\n🎤 Reply with a voice message."
    await message.answer(prefix + body, parse_mode="HTML")


async def _start_speaking(message: Message, state: FSMContext, test: dict[str, Any]) -> None:
    await state.set_state(ExamSessionStates.answering_speaking)
    await state.update_data(speaking_queue=_speaking_queue(test), speaking_index=0, speaking_answers=[])
    await message.answer(
        "The examiner will ask you questions one by one. Answer each with a <b>voice message</b> "
        "(text is accepted too, but pronunciation and fluency can then only be estimated).\n"
        "<i>Har bir savolga ovozli xabar bilan javob bering.</i>",
        parse_mode="HTML",
    )
    await _ask_speaking_question(message, state)


@router.message(ExamSessionStates.answering_speaking, F.voice | F.text)
async def handle_speaking_answer(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None:
        return
    data = await state.get_data()
    queue, idx = data["speaking_queue"], data["speaking_index"]

    if message.voice:
        tr = await usage_limits.consume(usage_limits.TRANSCRIBE, _subjects(message.from_user.id))
        if not tr.allowed:
            await message.answer("⏳ Daily speaking limit reached. Please come back tomorrow.")
            return
        file = await bot.get_file(message.voice.file_id)
        buffer = io.BytesIO()
        await bot.download_file(file.file_path, destination=buffer)  # type: ignore[arg-type]
        stt = await transcribe_voice_with_demo_fallback(
            audio_bytes=buffer.getvalue(),
            duration_seconds=float(message.voice.duration or 10),
            part_number=queue[idx]["part"],
            filename="voice.ogg",
        )
        text, duration = stt.transcribed_text.strip(), float(message.voice.duration or 10)
    else:
        text = (message.text or "").strip()
        duration = round(max(5.0, len(text.split()) / 130.0 * 60.0), 1)

    answers = data["speaking_answers"] + [{"part": queue[idx]["part"], "text": text, "duration": duration}]
    idx += 1
    await state.update_data(speaking_answers=answers, speaking_index=idx)
    if idx < len(queue):
        await _ask_speaking_question(message, state)
        return
    await _finish_speaking(message, state)


async def _finish_speaking(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    data = await state.get_data()
    exam_type: ExamType = data.get("exam_type", "IELTS")
    test = _get_active_test(exam_type, data.get("test_id"))
    sd = test["speaking_data"]

    decision = await usage_limits.consume(usage_limits.EXAM, _subjects(message.from_user.id))
    if not decision.allowed:
        await message.answer(LIMIT_REACHED_TEXT.format(limit=settings.DAILY_EXAM_LIMIT), parse_mode="HTML")
        await state.clear()
        return

    def joined(part: int) -> tuple[str, float]:
        items = [a for a in data["speaking_answers"] if a["part"] == part]
        return " ".join(a["text"] for a in items), sum(a["duration"] for a in items) or 10.0

    (p1, d1), (p2, d2), (p3, d3) = joined(1), joined(2), joined(3)
    wait = await message.answer("⏳ The AI examiner is assessing your speaking… / Baholanmoqda…")
    request = SpeakingEvaluationRequest(
        exam_type=exam_type,
        part_1=SpeakingPartInput(part_number=1, question_prompt="; ".join(sd["part_1_questions"]), transcript_text=p1, duration_seconds=d1),
        part_2=SpeakingPartInput(part_number=2, question_prompt=sd["part_2_cue_card"], transcript_text=p2, duration_seconds=d2),
        part_3=SpeakingPartInput(part_number=3, question_prompt="; ".join(sd["part_3_questions"]), transcript_text=p3, duration_seconds=d3),
    )
    try:
        result = await evaluate_speaking_with_demo_fallback(request, feedback_language=_feedback_language(message.from_user))
    except AIServiceUnavailableError:
        await usage_limits.refund(usage_limits.EXAM, _subjects(message.from_user.id))
        raise
    finally:
        await wait.delete()

    c = result.criteria_scores
    text = (
        f"📊 <b>Speaking result ({exam_type})</b>\n\n"
        f"Overall: <b>{_band_or_75(result.overall_speaking_score, exam_type)}</b>  (CEFR {result.cefr_level})\n"
        f"Fluency {c.fluency_coherence:.1f} • Vocabulary {c.lexical_resource:.1f} • "
        f"Grammar {c.grammatical_range_accuracy:.1f} • Pronunciation {c.pronunciation:.1f}\n\n"
        f"🗣 {html.escape(result.fluency_feedback_uz)}\n🔊 {html.escape(result.pronunciation_feedback_uz)}"
        + (f"\n\n🧑‍🏫 {html.escape(result.examiner_summary)}" if result.examiner_summary else "")
        + _format_errors_and_vocab(result.detailed_errors, result.band_booster_vocabulary)
        + "\n\n<i>Unofficial AI mock assessment — not an official IELTS/CEFR result.</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=build_main_menu_keyboard())
    await state.clear()


@router.message(StateFilter(ExamSessionStates.submitting_writing_task_1, ExamSessionStates.submitting_writing_task_2, ExamSessionStates.answering_speaking))
async def handle_unexpected_input(message: Message) -> None:
    await message.answer("Please send text, a photo (Writing) or a voice message (Speaking). /start to cancel.")



@router.errors(ExceptionTypeFilter(AIServiceUnavailableError))
async def handle_ai_unavailable_error(event: ErrorEvent) -> bool:
    """Tell the candidate to retry instead of silently failing; FSM state is kept so they can resend."""
    logger.warning("Exam flow submission failed: %s", event.exception)
    message = event.update.message or (
        event.update.callback_query.message if event.update.callback_query else None
    )
    if message is not None:
        await message.answer(
            "⚠️ The AI examiner could not process this answer right now. "
            "Please send it again in a minute.\n"
            "⚠️ AI baholovchi hozir javobni qayta ishlay olmadi. Iltimos, bir daqiqadan so'ng qayta yuboring."
        )
    return True


__all__ = [
    "AIServiceUnavailableError",
    "evaluate_speaking_with_demo_fallback",
    "evaluate_writing_with_demo_fallback",
    "is_placeholder_api_key",
    "router",
    "transcribe_image_with_demo_fallback",
    "transcribe_voice_with_demo_fallback",
]
