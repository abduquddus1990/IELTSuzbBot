"""Stage 6: simulate the chat-based Writing and Speaking practice flows with mocked Telegram objects."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import exam_flow
from app.bot.states.exam_states import ExamSessionStates
from app.core.config import settings

LONG_T1 = " ".join(["The chart shows that internet access grew in every country between 2015 and 2025."] * 12)
LONG_T2 = " ".join(["Many people believe that teachers will always be needed because they motivate students."] * 20)


def _user():
    return SimpleNamespace(id=4242, language_code="uz", full_name="Test")


def _message(text: str | None = None):
    msg = MagicMock()
    msg.text = text
    msg.photo = None
    msg.voice = None
    msg.from_user = _user()
    msg.answer = AsyncMock(return_value=MagicMock(delete=AsyncMock()))
    msg.answer_photo = AsyncMock()
    return msg


def _state() -> FSMContext:
    return FSMContext(storage=MemoryStorage(), key=StorageKey(bot_id=1, chat_id=4242, user_id=4242))


def _callback(data: str, message):
    cb = MagicMock()
    cb.data = data
    cb.message = message
    cb.from_user = _user()
    cb.answer = AsyncMock()
    return cb


@pytest.mark.anyio
async def test_writing_practice_flow_sends_chart_and_result():
    state = _state()
    menu_msg = _message()
    await exam_flow.cb_select_exam_type(_callback("exam_type:IELTS", menu_msg), state)
    await exam_flow.cb_select_exam_mode(_callback("mode:writing", menu_msg), state)
    menu_msg.answer_photo.assert_awaited()  # Task 1 visual is sent as an image
    assert await state.get_state() == ExamSessionStates.submitting_writing_task_1.state

    await exam_flow.handle_writing_task_1(_message(LONG_T1), state, bot=MagicMock())
    assert await state.get_state() == ExamSessionStates.submitting_writing_task_2.state

    final = _message(LONG_T2)
    await exam_flow.handle_writing_task_2(final, state, bot=MagicMock())
    result_text = final.answer.await_args_list[-1].kwargs.get("text") or final.answer.await_args_list[-1].args[0]
    assert "Writing result" in result_text
    assert await state.get_state() is None


@pytest.mark.anyio
async def test_speaking_practice_asks_every_question_one_by_one():
    state = _state()
    menu_msg = _message()
    await exam_flow.cb_select_exam_type(_callback("exam_type:CEFR", menu_msg), state)
    await exam_flow.cb_select_exam_mode(_callback("mode:speaking", menu_msg), state)
    data = await state.get_data()
    queue = data["speaking_queue"]
    assert len([q for q in queue if q["part"] == 1]) >= 8
    assert len([q for q in queue if q["part"] == 2]) == 1
    assert len([q for q in queue if q["part"] == 3]) >= 4

    answer = "I think this is an interesting question because people in my city often discuss it with their friends and family."
    last = None
    for _ in range(len(queue)):
        last = _message(answer)
        await exam_flow.handle_speaking_answer(last, state, bot=MagicMock())
    texts = [c.args[0] if c.args else c.kwargs.get("text", "") for c in last.answer.await_args_list]
    assert any("Speaking result" in t for t in texts)
    assert await state.get_state() is None


@pytest.mark.anyio
async def test_bot_respects_daily_limit(monkeypatch):
    monkeypatch.setattr(settings, "DAILY_EXAM_LIMIT", 0)
    state = _state()
    msg = _message()
    await exam_flow.cb_select_exam_type(_callback("exam_type:IELTS", msg), state)
    await exam_flow.cb_select_exam_mode(_callback("mode:writing", msg), state)
    texts = [c.args[0] if c.args else c.kwargs.get("text", "") for c in msg.answer.await_args_list]
    assert any("Daily limit reached" in t for t in texts)


def test_webhook_requires_secret_and_feeds_update_in_background(monkeypatch):
    import time

    from fastapi.testclient import TestClient

    from app import main

    fed = []

    async def fake_feed(bot, update):
        fed.append(update.update_id)

    monkeypatch.setattr(main.bot_dispatcher, "feed_update", fake_feed)
    client = TestClient(main.app)
    main.app.state.bot = MagicMock()
    update = {"update_id": 777, "message": {"message_id": 1, "date": 0, "chat": {"id": 1, "type": "private"}, "text": "/start"}}
    path = settings.BOT_WEBHOOK_PATH

    assert client.post(path, json=update).status_code == 401
    assert client.post(path, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}).status_code == 401
    ok = client.post(path, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": main.webhook_secret()})
    assert ok.status_code == 200
    for _ in range(50):
        if fed:
            break
        time.sleep(0.02)
    assert fed == [777]
    main.app.state.bot = None


def test_bot_mode_selection(monkeypatch):
    from app import main

    monkeypatch.delenv("BOT_MODE", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://example.onrender.com")
    assert main.bot_mode() == "webhook"
    assert main.webhook_url() == "https://example.onrender.com" + settings.BOT_WEBHOOK_PATH
    monkeypatch.delenv("RENDER_EXTERNAL_URL")
    monkeypatch.setenv("RUN_BOT_POLLING_IN_WEB", "true")
    assert main.bot_mode() == "polling"
    monkeypatch.setenv("BOT_MODE", "off")
    assert main.bot_mode() == "off"
