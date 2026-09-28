---
name: speaking-and-pdf-report
description: >-
  OpenAI Whisper (whisper-1) Speech-to-Text pipeline, IELTS & Uzbekistan BBA Multi-level CEFR
  Speaking evaluation rubrics (Part 1, 2, 3), Cloudflare R2 media storage, and ReportLab
  multi-page PDF Certificate & Error Workbook generation. Activate this skill when working on
  Speaking assessment, audio processing, R2 storage, or PDF report generation.
---

# Speaking Evaluation (Whisper + Claude) & ReportLab PDF Generation Skill

## 1. OpenAI Whisper (`whisper-1`) STT Pipeline for Speaking
- **Supported Formats:** Telegram `.ogg` (Opus), `.mp3`, `.wav`, `.m4a`, `.webm`. Pass as `(filename, audio_bytes, mime_type)` to `AsyncOpenAI().audio.transcriptions.create(model="whisper-1", ...)`.
- **Psychometric Fidelity:** Do NOT instruct Whisper to polish grammar. Use a conditioning prompt that preserves verbatim speech including hesitations (`uh`, `um`, `er`) so Fluency & Coherence can be measured accurately.
- **Speech Telemetry:** Calculate `word_count`, `duration_seconds`, `words_per_minute` (WPM: normal conversational English is 110–150 WPM), and `filler_word_count` for each part (Part 1, Part 2, Part 3).

## 2. IELTS & UzBMB Multi-Level (CEFR) Speaking Rubric
- **4 Criteria (25% weight each):**
  1. `fluency_coherence`: Speech rate, logical connectors, absence of long pauses/self-correction.
  2. `lexical_resource`: Idiomatic language, collocations, paraphrasing ability, topic vocabulary.
  3. `grammatical_range_accuracy`: Complex sentence structures, tense accuracy, error frequency.
  4. `pronunciation`: Intelligibility, word/sentence stress, rhythm, and clarity (inferred from STT confidence, phonetic misrecognitions, and prosodic markers).
- **Dual Scale Reporting:**
  - Always compute both `overall_speaking_score` on the `0.0 - 9.0` Band scale (0.5 increments) AND `standard_score_75` on the Uzbekistan BBA `0 - 75` scale (`65-75 = C1`, `51-64 = B2`, `38-50 = B1`, `<38 = BELOW_B1`).
- **Anti-Jailbreak:** Wrap Part 1, 2, 3 transcripts inside `<student_speaking_part_1>`, `<student_speaking_part_2>`, `<student_speaking_part_3>` XML tags and pre-screen with `check_prompt_injection`.

## 3. ReportLab Multi-Page PDF Certificate & Error Workbook ($0 API Cost)
- **Page 1 (Certificate & Executive Summary):**
  - Dark Navy/Gold modern header banner, Candidate info, Verification ID, and Exam Type badge.
  - Overall Score Hero Card showing IELTS Band (`0.0 - 9.0`), CEFR Level (`B1`/`B2`/`C1`), and BBA Standard Score (`0 - 75`).
  - 4-Skill Breakdown (Listening, Reading, Writing, Speaking) with vector progress bars (`Drawing` + `Rect`).
  - Writing & Speaking 4-criteria sub-scores.
  - Verification QR code (`QrCodeWidget` inside a `Drawing`).
  - Mandatory Legal Disclaimer footer: *"Mustaqil AI baholash va tayyorgarlik vositasi. Ushbu hujjat rasmiy Cambridge, IDP, British Council yoki Bilimni baholash agentligi (BBA) sertifikati hisoblanmaydi."*
- **Page 2+ (Xatolar Daftari & Band Booster Vocabulary):**
  - Structured tables for Writing & Speaking `detailed_errors` (`Xato jumla` | `To'g'ri shakl` | `O'zbekcha tushuntirish`).
  - Structured tables for `band_booster_vocabulary` (`Ishlatilgan oddiy so'z` | `Tavsiya etilgan C1 / Band 8+ muqobil`).
