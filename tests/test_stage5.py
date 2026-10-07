"""Stage 5: free tier limits, real exam content, Task 1 charts, signed reports and client safety."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import usage_limits
from app.services.chart_renderer import render_task1_chart
from app.services.content.writing_charts import TASK1_CHARTS
from app.services.demo_exam_bank import DEMO_TESTS, get_demo_test_by_id, sanitize_test_for_client
from app.services.report_tokens import decode_report_token, encode_report_token

client = TestClient(app)


@pytest.mark.parametrize("exam", DEMO_TESTS, ids=lambda e: e["id"])
def test_every_variant_has_complete_consistent_content(exam):
    for section in ("listening_data", "reading_data"):
        data = exam[section]
        numbers = sorted(q["number"] for q in data["questions"])
        assert numbers == list(range(1, 41))
        for q in data["questions"]:
            expected = data["answer_key"][q["id"]].split("/")[0]
            if "options" in q:
                assert expected in {o["value"] for o in q["options"]}, (exam["id"], q["id"])
            else:
                assert "____" in q["prompt"], (exam["id"], q["id"])
    for part in exam["listening_data"]["parts"]:
        assert part["audio_url"].endswith(".mp3")
    sd = exam["speaking_data"]
    assert len(sd["part_1_questions"]) >= 8
    assert len(sd["part_3_questions"]) >= 4
    if exam["exam_type"] == "IELTS":
        assert exam["id"] in TASK1_CHARTS


def test_listening_audio_files_exist():
    from app.core.config import BASE_DIR

    for exam in DEMO_TESTS[:2]:
        for part in exam["listening_data"]["parts"]:
            path = BASE_DIR / part["audio_url"].lstrip("/")
            assert path.is_file() and path.stat().st_size > 50_000, path


def test_client_payload_hides_answers_and_audio_scripts():
    raw = get_demo_test_by_id("IELTS-MOCK-01")
    text = json.dumps(sanitize_test_for_client(raw))
    assert "answer_key" not in text
    assert '"script"' not in text
    assert "task_1_chart_text" not in text
    assert "Fairbrook" not in text  # an answer that only appears in the audio script


def test_task1_chart_renders_png_and_endpoint():
    png = render_task1_chart("IELTS-MOCK-03")
    assert png and png.startswith(b"\x89PNG")
    resp = client.get("/api/v1/tests/IELTS-MOCK-03/task1-chart.png")
    assert resp.status_code == 200 and resp.headers["content-type"] == "image/png"
    assert client.get("/api/v1/tests/CEFR-MOCK-01/task1-chart.png").status_code == 404


def test_report_token_roundtrip_and_tamper_detection():
    token = encode_report_token({"report_id": "X-1", "scores": {"overall_band": 6.5}})
    assert decode_report_token(token)["scores"]["overall_band"] == 6.5
    with pytest.raises(ValueError):
        decode_report_token(token[:-4] + "abcd")


@pytest.mark.anyio
async def test_quota_consume_limit_and_refund(monkeypatch):
    monkeypatch.setattr(settings, "DAILY_EXAM_LIMIT", 2)
    subjects = ["web:abcdefgh12", "ip:1.2.3.4"]
    assert (await usage_limits.consume(usage_limits.EXAM, subjects)).allowed
    assert (await usage_limits.consume(usage_limits.EXAM, subjects)).allowed
    blocked = await usage_limits.consume(usage_limits.EXAM, subjects)
    assert not blocked.allowed and blocked.remaining == 0
    await usage_limits.refund(usage_limits.EXAM, subjects)
    assert (await usage_limits.remaining(usage_limits.EXAM, subjects)).remaining == 1
    # another browser on the same IP still has its own allowance (IP cap is higher)
    assert (await usage_limits.consume(usage_limits.EXAM, ["web:zzzzzzzz99", "ip:1.2.3.4"])).allowed


def test_daily_limit_enforced_on_api(monkeypatch):
    monkeypatch.setattr(settings, "DAILY_EXAM_LIMIT", 1)
    headers = {"X-Client-Id": "limit-test-client-01"}
    assert client.get("/api/v1/quota", headers=headers).json()["remaining"] == 1
    body = {"test_id": "IELTS-MOCK-01", "exam_type": "IELTS", "task_1_text": "short", "task_2_text": "short"}
    first = client.post("/api/v1/submissions/writing", headers=headers, json=body)
    assert first.status_code == 200
    second = client.post("/api/v1/submissions/writing", headers=headers, json=body)
    assert second.status_code == 429
    # Listening/Reading scoring stays unlimited
    obj = client.post("/api/v1/submissions/objective", headers=headers, json={"test_id": "IELTS-MOCK-01", "reading_answers": {"1": "TRUE"}})
    assert obj.status_code == 200 and obj.json()["reading"]["correct_count"] == 1


def test_failed_ai_call_is_refunded(monkeypatch):
    from app.api.v1 import exams
    from app.bot.handlers.exam_flow import AIServiceUnavailableError

    async def broken(*_args, **_kwargs):
        raise AIServiceUnavailableError("down")

    monkeypatch.setattr(settings, "DAILY_EXAM_LIMIT", 1)
    monkeypatch.setattr(exams, "evaluate_writing_with_demo_fallback", broken)
    headers = {"X-Client-Id": "refund-test-client-01"}
    body = {"test_id": "IELTS-MOCK-01", "task_1_text": "a", "task_2_text": "b"}
    resp = client.post("/api/v1/submissions/writing", headers=headers, json=body)
    assert resp.status_code == 503
    assert client.get("/api/v1/quota", headers=headers).json()["remaining"] == 1


def test_public_config_and_root_redirect():
    cfg = client.get("/api/v1/config").json()
    assert cfg["daily_exam_limit"] == settings.DAILY_EXAM_LIMIT
    assert "ads" in cfg
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 307) and resp.headers["location"] == "/webapp/"
    assert client.get("/api/v1/payments/config").status_code == 404  # platform is free


@pytest.mark.anyio
async def test_missing_task_scores_zero_but_other_task_is_still_marked(monkeypatch):
    from app.bot.handlers import exam_flow
    from app.schemas.writing import CriteriaScores, WritingEvaluationRequest, WritingEvaluationResult

    seen = {}

    async def fake_ai(request, t1, t2, lang):
        seen["t1"] = t1
        return WritingEvaluationResult(
            exam_type="IELTS", task_1_score=5.0, task_2_score=6.0, overall_writing_score=6.0, cefr_level="B2",
            criteria_scores=CriteriaScores(task_achievement=6, coherence_cohesion=6, lexical_resource=6, grammatical_range_accuracy=6),
            examiner_summary="ok",
        )

    monkeypatch.setattr(exam_flow, "_evaluate_writing_texts", fake_ai)
    req = WritingEvaluationRequest.model_validate({"exam_type": "IELTS", "task_1_prompt": "Chart", "task_1_text": "", "task_2_prompt": "Essay", "task_2_text": "A real essay about education and technology."})
    result = await exam_flow.evaluate_writing_with_demo_fallback(req)
    assert seen["t1"] == exam_flow.NO_RESPONSE_PLACEHOLDER
    assert result.task_1_score == 0.0 and result.task_2_score == 6.0
    assert result.overall_writing_score > 0
