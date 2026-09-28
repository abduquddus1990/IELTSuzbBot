---
name: telegram-bot-and-webapp
description: >-
  aiogram 3.x Telegram Bot FSM workflows, FastAPI REST & Webhook endpoints,
  Telegram WebApp (Mini App) HMAC-SHA256 initData security, and interactive
  Listening/Reading/Writing exam interface guidelines. Activate this skill when
  working on app/bot/, app/api/, or webapp/.
---

# Telegram Bot (aiogram 3) + FastAPI + Mini App (WebApp) Skill

## 1. Telegram Bot (`aiogram 3.x`) Exam Flow & FSM States
- **FSM States (`ExamSessionStates`):**
  1. `choosing_exam_type`: Candidate selects `IELTS Academic` or `CEFR Multi-Level (UzBMB)`.
  2. `taking_listening_reading`: Candidate completes 40 Listening & 40 Reading questions via Telegram Mini App (`WebAppInfo`) or quick bot mode.
  3. `submitting_writing_task_1`: Candidate sends Task 1 text OR a photo of their handwritten notebook essay (processed via Vision OCR).
  4. `submitting_writing_task_2`: Candidate sends Task 2 text OR a photo of their handwritten essay.
  5. `submitting_speaking_part_1`: Candidate sends `.ogg` voice message (or text in test mode) for Part 1.
  6. `submitting_speaking_part_2`: Candidate sends `.ogg` voice message for Part 2 (Cue Card / Situation).
  7. `submitting_speaking_part_3`: Candidate sends `.ogg` voice message for Part 3 (Abstract Discussion).
- **PDF Delivery:**
  - Use `BufferedInputFile(file=pdf_bytes, filename=f"{report_id}.pdf")` with `message.answer_document()` to deliver the 2-3 page PDF Certificate & Error Workbook directly to the user in Telegram.

## 2. Telegram WebApp (`initData`) HMAC-SHA256 Security
- Compute `secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()`.
- Sort all `initData` query parameters (excluding `hash`) alphabetically as `key=value` joined by `\n`.
- Verify `hmac.compare_digest(computed_hash, provided_hash)`.
- Provide a clean dev-mode bypass (`DEBUG=True`) when testing in a local browser outside Telegram.

## 3. FastAPI REST API Endpoints (`app/api/v1/`)
- `GET /api/v1/health`: Health & readiness check.
- `GET /api/v1/tests`: List available active `IELTS` and `CEFR` mock exams (from DB or built-in Demo Exam Bank).
- `GET /api/v1/tests/{test_id}`: Fetch exam questions (without exposing `answer_key` to the client!).
- `POST /api/v1/submissions/objective`: Grade 40 Listening & 40 Reading answers at `$0.00` token cost.
- `POST /api/v1/submissions/writing`: Evaluate Task 1 & Task 2 (text or base64/uploaded image with Vision OCR).
- `POST /api/v1/submissions/speaking`: Transcribe `.ogg`/`.mp3` via Whisper & evaluate Part 1, 2, 3 via Claude.
- `POST /api/v1/submissions/full-report`: Compile all 4 skills, calculate Overall IELTS `.25`/`.75` Band & BBA `0-75` score, and return/download the generated PDF report.
- `GET /api/v1/reports/{report_id}/pdf`: Download generated PDF report directly.
