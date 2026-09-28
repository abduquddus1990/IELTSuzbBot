# 🎓 IELTS & CEFR Mock AI — Avtomatlashtirilgan EdTech Platformasi

**IELTS & CEFR Mock AI** — Telegram ekotizimi (Bot + WebApp Mini App) orqali xalqaro **IELTS (0.0 – 9.0 Band)** hamda O'zbekiston milliy **CEFR / Multi-level (B1, B2, C1)** imtihonlaridan to'liq formatda sinov (Mock) topshirish, AI yordamida chuqur tahlil olish va PDF sertifikat/hisobot shakllantirish platformasi.

---

## 🏗️ 1. Loyiha Arxitekturasi (Clean Architecture & Repository Pattern)

```text
ielts-cefr-mock-ai/
├── .agents/
│   └── skills/
│       ├── ielts-cefr-evaluator/SKILL.md     # Rasmiy IELTS/CEFR baholash va Anti-Jailbreak qoidalari
│       └── fastapi-aiogram-clean-arch/SKILL.md # Clean Architecture & Async DB standarti
├── app/
│   ├── api/                                  # FastAPI REST endpoints & Webhooks
│   │   └── v1/                               # Telegram, Click, Payme va Mini App API'lari
│   ├── bot/                                  # aiogram 3.x Telegram Bot qatlami
│   │   ├── handlers/                         # Start, Exam, Payment, Profile handlerlari
│   │   ├── keyboards/                        # Inline & Reply tugmalar (WebApp integratsiyasi)
│   │   ├── middlewares/                      # Auth, Throttling, DB session middleware
│   │   └── states/                           # FSM holatlari (Writing, Speaking topshirish)
│   ├── core/
│   │   └── config.py                         # Pydantic BaseSettings (.env konfiguratsiyasi)
│   ├── db/
│   │   ├── base.py                           # SQLAlchemy 2.0 DeclarativeBase & Mixins
│   │   └── session.py                        # AsyncEngine & AsyncSession (Neon/Supabase)
│   ├── models/                               # PostgreSQL Jadvallari (SQLAlchemy 2.0)
│   │   ├── enums.py                          # ExamType, CEFRLevel, SubmissionStatus va h.k.
│   │   ├── user.py                           # User va PaymentTransaction modellari
│   │   ├── test.py                           # MockTest (Listening, Reading, Writing, Speaking)
│   │   ├── submission.py                     # TestSubmission (Javoblar, OCR matnlar, Audio R2)
│   │   └── score.py                          # ExamScore (Barcha ballar, Xatolar tahlili, PDF)
│   ├── repositories/                         # Repository Pattern (DB CRUD abstraksiyasi)
│   │   ├── base.py                           # Generic Async BaseRepository
│   │   ├── user_repo.py
│   │   ├── test_repo.py
│   │   ├── submission_repo.py
│   │   └── score_repo.py
│   ├── schemas/                              # Pydantic v2 ma'lumotlar validatsiyasi
│   │   └── writing.py                        # Qat'iy JSON kontrakt (Claude javob sxemasi)
│   ├── services/                             # Biznes mantiq va AI integratsiyalar
│   │   ├── writing_evaluator.py              # Claude API Writing baholash + Vision OCR + Anti-Cheat
│   │   └── reading_listening_scorer.py       # $0.00 Token Listening & Reading tekshiruvchi
│   ├── utils/                                # Yordamchi funksiyalar
│   └── main.py                               # FastAPI + aiogram 3 kirish nuqtasi
├── storage/
│   └── reports/                              # Generatsiya qilingan PDF hisobotlar
├── tests/
│   └── test_stage1.py                        # 1-bosqich avtotestlari
├── webapp/                                   # Telegram Mini App (Frontend)
├── .env                                      # Maxfiy tokenlar va parollar fayli (Git'ga tushmaydi)
├── .env.example                              # Konfiguratsiya namunasi
├── GEMINI.md                                 # Loyiha konstitutsiyasi va AI qoidalari
└── requirements.txt                          # Python kutubxonalari ro'yxati
```

---

## 🔑 2. Token va Parollarni Kiritish

Barcha maxfiy kalitlar loyiha ildizidagi [`.env`](file:///C:/Users/Surface/.gemini/antigravity/scratch/ielts-cefr-mock-ai/.env) fayliga kiritiladi:
1. `BOT_TOKEN` — `@BotFather` dan olingan Telegram bot tokeni.
2. `DATABASE_URL` — Supabase yoki Neon.tech bepul PostgreSQL bazasi havolasi.
3. `ANTHROPIC_API_KEY` — Writing/Speaking baholash va Vision OCR uchun Claude API kaliti.
4. `OPENAI_API_KEY` — Speaking (`whisper-1`) transkripsiyasi uchun OpenAI API kaliti.
5. `R2_*` — Cloudflare R2 audio va rasm saqlash kalitlari.
6. `CLICK_*` va `PAYME_*` — To'lov tizimlari kalitlari.

---

## 🚀 3. Ishga Tushirish

```bash
# 1. Virtual muhit yaratish va faollashtirish
python -m venv .venv
.venv\Scripts\activate

# 2. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. Testlarni tekshirish
pytest tests/test_stage1.py -v

# 4. Serverni ishga tushirish
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Yuridik eslatma:** Ushbu platforma mustaqil AI baholash va tayyorgarlik vositasi hisoblanadi. Rasmiy Cambridge, IDP, British Council yoki O'zbekiston Bilimni baholash agentligi (BBA) sertifikati o'rnini bosmaydi.
