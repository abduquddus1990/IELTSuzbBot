"""Comprehensive Stage 3 unit & integration tests for Telegram Bot, FastAPI REST API, and Mini App.

Covers:
1. Telegram WebApp `initData` HMAC-SHA256 authentication (`create_signed_webapp_init_data` &
   `verify_telegram_webapp_init_data`: valid signature, tampered hash, tampered user, expired `auth_date`).
2. Built-in Demo Exam Bank (`get_demo_tests`, `get_demo_test_by_id`, and `sanitize_test_for_client`,
   verifying `answer_key` is present in raw server data and stripped from client-facing payloads).
3. FastAPI REST API endpoints (`GET /api/v1/health`, `GET /api/v1/tests`, `GET /api/v1/tests/IELTS-MOCK-01`,
   `POST /api/v1/submissions/objective`, `POST /api/v1/submissions/full-report`, and
   `GET /api/v1/reports/{report_id}/pdf` returning valid `%PDF-` bytes).
4. `aiogram 3.x` FSM states (`ExamSessionStates`) and keyboards (`build_main_menu_keyboard`,
   `build_exam_type_keyboard`, `build_exam_mode_keyboard`).
5. Existence, structure, and mandatory legal disclaimer of `webapp/index.html`, `webapp/styles.css`,
   and `webapp/app.js`.
"""

from __future__ import annotations

import inspect
import json
import time
from typing import Any

import pytest
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from fastapi.testclient import TestClient

from app.bot.keyboards import (
    build_exam_mode_keyboard,
    build_exam_type_keyboard,
    build_main_menu_keyboard,
)
from app.bot.states import ExamSessionStates
from app.core.config import BASE_DIR, settings
from app.main import app, create_app
from app.services.demo_exam_bank import (
    get_demo_test_by_id,
    get_demo_tests,
    sanitize_test_for_client,
)
from app.utils.telegram_auth import (
    compute_webapp_secret_key,
    create_signed_webapp_init_data,
    verify_telegram_webapp_init_data,
)

SAMPLE_TASK_1_TEXT = (
    "The bar chart illustrates the percentage of households with access to high-speed fiber-optic "
    "internet and residential solar power across South Korea, Germany, Uzbekistan, and Brazil "
    "between 2015 and 2025. Overall, all four nations experienced a marked upward trajectory in "
    "both digital connectivity and renewable energy adoption over the ten-year period, with South "
    "Korea consistently maintaining the highest internet penetration rate while Uzbekistan recorded "
    "the fastest relative growth."
)

SAMPLE_TASK_2_TEXT = (
    "In the modern era, the rapid rise of artificial intelligence tutoring systems and online "
    "education platforms has sparked debate over whether technology will eventually replace human "
    "classroom teachers. While automated learning tools provide remarkable flexibility and tailored "
    "practice for individual students, I firmly believe that physical classroom educators remain "
    "indispensable for nurturing critical thinking, empathy, collaborative problem-solving, and "
    "social discipline among young learners."
)

SAMPLE_SPEAKING_P1 = (
    "I am currently a university student in Tashkent studying computer science. I organize my daily "
    "schedule using digital calendars and dedicate every morning to academic English practice."
)

SAMPLE_SPEAKING_P2 = (
    "I would like to describe a challenging scheduling problem our university engineering team "
    "solved using a cloud-based project management tool. By tracking milestones transparently, we "
    "delivered our prototype two weeks ahead of the deadline."
)

SAMPLE_SPEAKING_P3 = (
    "Technology has significantly expanded access to university preparation resources across "
    "Uzbekistan, allowing students in regional towns to practice with interactive mock assessments."
)


# =====================================================================
# 1. TELEGRAM WEBAPP HMAC-SHA256 AUTHENTICATION TESTS
# =====================================================================


def test_telegram_webapp_init_data_valid_signature() -> None:
    """Verify valid HMAC-SHA256 signed initData passes verification and extracts user payload."""
    bot_token = "1234567890:AAH_test_secret_bot_token_for_hmac"
    user_payload = {
        "id": 998901234567,
        "first_name": "Azizbek",
        "last_name": "Karimov",
        "username": "azizbek_ielts",
        "language_code": "uz",
    }
    now_ts = int(time.time())

    init_data = create_signed_webapp_init_data(
        user_data=user_payload,
        bot_token=bot_token,
        auth_date=now_ts,
    )
    assert "hash=" in init_data
    assert "auth_date=" in init_data
    assert "user=" in init_data

    verified = verify_telegram_webapp_init_data(
        init_data=init_data,
        bot_token=bot_token,
        max_age_seconds=3600,
    )
    assert verified["auth_date"] == now_ts
    assert verified["user"]["id"] == 998901234567
    assert verified["user"]["first_name"] == "Azizbek"
    assert verified["user"]["username"] == "azizbek_ielts"
    assert len(compute_webapp_secret_key(bot_token)) == 32


def test_telegram_webapp_init_data_rejects_tampered_hash_and_expired_auth_date() -> None:
    """Verify tampered hash, modified user data, or expired auth_date raise ValueError."""
    bot_token = "1234567890:AAH_test_secret_bot_token_for_hmac"
    user_payload = {"id": 11223344, "first_name": "Malika"}

    valid_init_data = create_signed_webapp_init_data(
        user_data=user_payload,
        bot_token=bot_token,
    )

    # 1. Tamper with the hexadecimal hash signature
    tampered_hash_data = valid_init_data[:-4] + ("0000" if not valid_init_data.endswith("0000") else "ffff")
    with pytest.raises(ValueError, match="signature|hash|Invalid"):
        verify_telegram_webapp_init_data(tampered_hash_data, bot_token=bot_token)

    # 2. Verify with wrong bot token
    with pytest.raises(ValueError, match="signature|Invalid"):
        verify_telegram_webapp_init_data(valid_init_data, bot_token="999999:WRONG_TOKEN")

    # 3. Expired auth_date (older than max_age_seconds)
    expired_ts = int(time.time()) - 7200
    expired_init_data = create_signed_webapp_init_data(
        user_data=user_payload,
        bot_token=bot_token,
        auth_date=expired_ts,
    )
    with pytest.raises(ValueError, match="expired"):
        verify_telegram_webapp_init_data(
            expired_init_data,
            bot_token=bot_token,
            max_age_seconds=3600,
        )


# =====================================================================
# 2. DEMO EXAM BANK & CLIENT SANITIZATION TESTS
# =====================================================================


def test_demo_exam_bank_and_client_sanitization() -> None:
    """Verify Demo Exam Bank contains 10 IELTS & 10 CEFR random variants and strips answer_key for clients."""
    all_tests = get_demo_tests()
    assert len(all_tests) == 20
    test_ids = {t["id"] for t in all_tests}
    assert "IELTS-MOCK-01" in test_ids
    assert "IELTS-MOCK-10" in test_ids
    assert "CEFR-MOCK-01" in test_ids
    assert "CEFR-MOCK-10" in test_ids

    ielts_only = get_demo_tests(exam_type="IELTS")
    assert len(ielts_only) == 10
    assert all(t["exam_type"] == "IELTS" for t in ielts_only)

    cefr_only = get_demo_tests(exam_type="CEFR")
    assert len(cefr_only) == 10
    assert all(t["exam_type"] == "CEFR" for t in cefr_only)

    # Verify random variant aliases
    rnd_ielts = get_demo_test_by_id("IELTS-RANDOM")
    assert rnd_ielts is not None and rnd_ielts["exam_type"] == "IELTS"
    rnd_cefr = get_demo_test_by_id("CEFR-RANDOM")
    assert rnd_cefr is not None and rnd_cefr["exam_type"] == "CEFR"

    raw_ielts = get_demo_test_by_id("IELTS-MOCK-01")
    assert raw_ielts is not None
    assert "answer_key" in raw_ielts["listening_data"]
    assert "answer_key" in raw_ielts["reading_data"]
    assert len(raw_ielts["listening_data"]["answer_key"]) == 40
    assert len(raw_ielts["reading_data"]["answer_key"]) == 40
    assert len(raw_ielts["listening_data"]["questions"]) == 40
    assert len(raw_ielts["reading_data"]["questions"]) == 40

    sanitized = sanitize_test_for_client(raw_ielts)
    assert "answer_key" not in sanitized
    assert "answer_key" not in sanitized["listening_data"]
    assert "answer_key" not in sanitized["reading_data"]
    assert "answer_key" not in json.dumps(sanitized)

    # Ensure original dictionary was not mutated
    assert "answer_key" in raw_ielts["listening_data"]
    assert "answer_key" in raw_ielts["reading_data"]


# =====================================================================
# 3. FASTAPI REST ENDPOINTS INTEGRATION TESTS
# =====================================================================


def test_fastapi_health_and_tests_endpoints_do_not_leak_answer_key() -> None:
    """Verify /api/v1/health, /api/v1/tests, and /api/v1/tests/IELTS-MOCK-01 work and hide answer_key."""
    fastapi_app = create_app() if callable(create_app) else app
    client = TestClient(fastapi_app)

    # 1. Health endpoint
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    health_json = health_resp.json()
    assert health_json.get("status") == "ok"

    # 2. List tests endpoint
    list_resp = client.get("/api/v1/tests")
    assert list_resp.status_code == 200
    list_raw_text = list_resp.text
    assert "answer_key" not in list_raw_text
    list_data = list_resp.json()
    tests_list = list_data["tests"] if isinstance(list_data, dict) and "tests" in list_data else list_data
    assert isinstance(tests_list, list)
    assert len(tests_list) >= 2

    # 3. Single test endpoint (IELTS-MOCK-01)
    detail_resp = client.get("/api/v1/tests/IELTS-MOCK-01")
    assert detail_resp.status_code == 200
    assert "answer_key" not in detail_resp.text
    detail_json = detail_resp.json()
    test_obj = detail_json["test"] if isinstance(detail_json, dict) and "test" in detail_json else detail_json
    assert test_obj["id"] == "IELTS-MOCK-01"
    assert "answer_key" not in test_obj.get("listening_data", {})
    assert "answer_key" not in test_obj.get("reading_data", {})
    assert len(test_obj["listening_data"]["questions"]) == 40
    assert len(test_obj["reading_data"]["questions"]) == 40


def test_fastapi_objective_submission_zero_cost_grading() -> None:
    """Verify POST /api/v1/submissions/objective grades Listening & Reading at $0.00 token cost."""
    fastapi_app = create_app() if callable(create_app) else app
    client = TestClient(fastapi_app)

    raw_ielts = get_demo_test_by_id("IELTS-MOCK-01")
    assert raw_ielts is not None
    l_key: dict[str, str] = raw_ielts["listening_data"]["answer_key"]
    r_key: dict[str, str] = raw_ielts["reading_data"]["answer_key"]

    # Prepare 30/40 correct Listening answers (Band 7.0) and 30/40 correct Reading answers (Band 7.0)
    listening_answers = {
        str(i): (l_key[str(i)] if i <= 30 else "wrong_answer")
        for i in range(1, 41)
    }
    reading_answers = {
        str(i): (r_key[str(i)] if i <= 30 else "wrong_answer")
        for i in range(1, 41)
    }

    init_data = create_signed_webapp_init_data(
        user_data={"id": 998901234567, "first_name": "Azizbek"},
        bot_token=settings.BOT_TOKEN,
    )

    resp = client.post(
        "/api/v1/submissions/objective",
        headers={"X-Telegram-Init-Data": init_data},
        json={
            "test_id": "IELTS-MOCK-01",
            "exam_type": "IELTS",
            "listening_answers": listening_answers,
            "reading_answers": reading_answers,
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    listening_res = data.get("listening", data)
    reading_res = data.get("reading", data)

    assert listening_res.get("correct_count") == 30
    assert listening_res.get("band_score") == 7.0
    assert listening_res.get("api_cost_usd", 0.0) == 0.0

    assert reading_res.get("correct_count") == 30
    assert reading_res.get("band_score") == 7.0
    assert reading_res.get("api_cost_usd", 0.0) == 0.0


def test_fastapi_full_report_generation_and_pdf_download() -> None:
    """Verify POST /api/v1/submissions/full-report compiles 4 skills and serves %PDF- via GET."""
    fastapi_app = create_app() if callable(create_app) else app
    client = TestClient(fastapi_app)

    raw_ielts = get_demo_test_by_id("IELTS-MOCK-01")
    assert raw_ielts is not None
    l_key: dict[str, str] = raw_ielts["listening_data"]["answer_key"]
    r_key: dict[str, str] = raw_ielts["reading_data"]["answer_key"]

    # 33/40 Listening (Band 7.5) and 30/40 Reading (Band 7.0)
    listening_answers = {str(i): (l_key[str(i)] if i <= 33 else "wrong") for i in range(1, 41)}
    reading_answers = {str(i): (r_key[str(i)] if i <= 30 else "wrong") for i in range(1, 41)}

    init_data = create_signed_webapp_init_data(
        user_data={"id": 998901234567, "first_name": "Azizbek"},
        bot_token=settings.BOT_TOKEN,
    )

    payload: dict[str, Any] = {
        "test_id": "IELTS-MOCK-01",
        "exam_type": "IELTS",
        "candidate_name": "Azizbek Karimov",
        "candidate_telegram_id": 998901234567,
        "listening_answers": listening_answers,
        "reading_answers": reading_answers,
        "writing_task_1_text": SAMPLE_TASK_1_TEXT,
        "writing_task_2_text": SAMPLE_TASK_2_TEXT,
        "task_1_text": SAMPLE_TASK_1_TEXT,
        "task_2_text": SAMPLE_TASK_2_TEXT,
        "speaking_part_1_text": SAMPLE_SPEAKING_P1,
        "speaking_part_2_text": SAMPLE_SPEAKING_P2,
        "speaking_part_3_text": SAMPLE_SPEAKING_P3,
        "part_1_text": SAMPLE_SPEAKING_P1,
        "part_2_text": SAMPLE_SPEAKING_P2,
        "part_3_text": SAMPLE_SPEAKING_P3,
    }

    full_resp = client.post(
        "/api/v1/submissions/full-report",
        headers={"X-Telegram-Init-Data": init_data},
        json=payload,
    )
    assert full_resp.status_code == 200
    report_json = full_resp.json()

    report_id = report_json.get("report_id") or report_json.get("report_data", {}).get("report_id")
    assert report_id is not None and len(str(report_id)) > 3

    scores = report_json.get("scores") or report_json.get("report_data", {}).get("scores") or {}
    assert scores.get("listening_band") == 7.5
    assert scores.get("reading_band") == 7.0
    assert scores.get("overall_band") >= 6.0
    assert scores.get("overall_score_75") >= 50.0
    assert scores.get("cefr_level") in {"B2", "C1", "C2"}

    # Download the generated PDF via GET /api/v1/reports/{report_id}/pdf
    pdf_resp = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_resp.status_code == 200
    assert "application/pdf" in pdf_resp.headers.get("content-type", "")
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 3072


# =====================================================================
# 4. AIOGRAM 3 BOT FSM STATES & KEYBOARDS TESTS
# =====================================================================


def test_aiogram_fsm_states_and_keyboards() -> None:
    """Verify ExamSessionStates FSM group and keyboard builders for Telegram Bot."""
    assert issubclass(ExamSessionStates, StatesGroup)

    required_states = [
        "choosing_exam_type",
        "taking_listening_reading",
        "submitting_writing_task_1",
        "submitting_writing_task_2",
        "submitting_speaking_part_1",
        "submitting_speaking_part_2",
        "submitting_speaking_part_3",
    ]
    for state_name in required_states:
        attr = getattr(ExamSessionStates, state_name, None)
        assert attr is not None, f"Missing FSM state: {state_name}"
        assert isinstance(attr, State)

    # Test keyboard builders
    main_kb = build_main_menu_keyboard()
    assert isinstance(main_kb, (InlineKeyboardMarkup, ReplyKeyboardMarkup))

    exam_type_kb = build_exam_type_keyboard()
    assert isinstance(exam_type_kb, (InlineKeyboardMarkup, ReplyKeyboardMarkup))

    mode_sig = inspect.signature(build_exam_mode_keyboard)
    if "exam_type" in mode_sig.parameters:
        exam_mode_kb = build_exam_mode_keyboard(exam_type="IELTS")
    else:
        exam_mode_kb = build_exam_mode_keyboard()
    assert isinstance(exam_mode_kb, (InlineKeyboardMarkup, ReplyKeyboardMarkup))


# =====================================================================
# 5. TELEGRAM MINI APP (WEBAPP) FRONTEND ASSETS STRUCTURE TESTS
# =====================================================================


def test_webapp_frontend_files_existence_and_structure() -> None:
    """Verify webapp/index.html, webapp/styles.css, and webapp/app.js exist and meet UI requirements."""
    webapp_dir = BASE_DIR / "webapp"
    index_html = webapp_dir / "index.html"
    styles_css = webapp_dir / "styles.css"
    app_js = webapp_dir / "app.js"

    assert index_html.exists() and index_html.stat().st_size > 2000
    assert styles_css.exists() and styles_css.stat().st_size > 500
    assert app_js.exists() and app_js.stat().st_size > 2000

    html_content = index_html.read_text(encoding="utf-8")
    css_content = styles_css.read_text(encoding="utf-8")
    js_content = app_js.read_text(encoding="utf-8")

    # Verify Telegram WebApp SDK & TailwindCSS in index.html
    assert "https://telegram.org/js/telegram-web-app.js" in html_content
    assert "IELTS" in html_content and "CEFR" in html_content
    assert "60:00" in html_content
    assert "Listening (40 savol)" in html_content
    assert "Reading (40 savol)" in html_content
    assert "Writing (Task 1" in html_content
    assert "150+" in html_content and "250+" in html_content
    assert "Mustaqil AI baholash va tayyorgarlik vositasi" in html_content

    # Verify custom classes in styles.css
    assert ".glass-card" in css_content
    assert ".nav-q-btn" in css_content
    assert ".timer-warning" in css_content

    # Verify REST API endpoints & Vision OCR base64 handling in app.js
    assert "/api/v1/tests/" in js_content
    assert "/api/v1/submissions/objective" in js_content
    assert "/api/v1/submissions/full-report" in js_content
    assert "/api/v1/reports/" in js_content
    assert "readAsDataURL" in js_content
