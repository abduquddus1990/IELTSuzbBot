# IELTS & CEFR Mock AI — Asosiy Loyiha Qoidalari va Arxitektura Konstitutsiyasi (GEMINI.md)

Ushbu fayl loyihaning doimiy xotirasi va qat'iy ishlash qoidalarini belgilaydi. Agent har bir buyruqni bajarishda ushbu qoidalarga so'zsiz amal qilishi shart.

---

## 0. AGENT ISHLASH PROTOKOLI (DOIMIY QOIDALAR)
1. **Asosiy Promptni Unutmaslik:** Loyiha maqsadi, tejamkor stack ($0 doimiy xarajat tamoyili), modullar mantig'i va xavfsizlik talablari hech qachon unutmasligi va buzilmasligi shart.
2. **Live Internet Research:** Har yangi buyruq olganda, eng so'nggi kutubxona versiyalari, API o'zgarishlari, baholash mezonlari yoki texnik yechimlarni internetdan (`search_web` / `read_url_content`) live rejimda tekshirib, aniqlik kiritib ishlash.
3. **Professional Meta-Prompt va Rollar:** Har bir yangi vazifa/buyruq olganda, ishni boshlashdan oldin:
   - Vazifa uchun maxsus **Professional Prompt** (Maqsad, Kontekst, Cheklovlar, Kutilayotgan Natija) tuzib olish;
   - Tegishli **Ekspert Rollarini** (masalan: *Senior Backend Architect*, *AI Prompt Security Engineer*, *EdTech Psychometrician*) belgilab olish.
4. **Skills (Ko'nikmalar) Yuklab Olish va Yaratish:** Har bir vazifa turiga mos ravishda `.agents/skills/<skill-name>/SKILL.md` ichida maxsus ko'nikmalar bazasini shakllantirish, yangilash va ulardan foydalanish.
5. **Maxsus Subagentlar (Multi-Agent Orchestration):** Murakkab vazifalarni bajarishda `define_subagent` va `invoke_subagent` orqali ixtisoslashgan subagentlar yaratib, ishlarni parallel va sifatli bajarish.
6. **Aniqlik Kiritish (Clarification):** Agar foydalanuvchi buyrug'ida noaniqlik bo'lsa yoki biznes mantiqni to'ldirish kerak bo'lsa, taxmin qilmasdan foydalanuvchidan savol so'rab aniqlashtirish.

---

## 1. LOYIHA MAQSADI VA KONSEPSIYASI
Platforma foydalanuvchilarga rasmiy xalqaro **IELTS (0.0 - 9.0 Band)** hamda O'zbekiston milliy **CEFR / Multi-level (B1, B2, C1 — 0-75 shkala)** imtihonlari formatida to'liq sinov topshirish imkonini beradi. Natijada xatolar tahlili, so'z boyligi bo'yicha tavsiyalar va rasmiy baholash rubrikasi asosida batafsil PDF hisobot yaratiladi.

---

## 2. TEJAMKOR TEXNOLOGIK STACK
- **Backend:** Python 3.11+ (FastAPI) + `aiogram 3.x` (Telegram bot)
- **Database:** PostgreSQL (Supabase / Neon serverless) + SQLAlchemy 2.0 (Async) + Alembic
- **Frontend:** Telegram WebApp / Mini App (HTML/TailwindCSS/Vanilla JS yoki Vite + React — Vercel/Cloudflare Pages)
- **Storage:** Cloudflare R2 (`boto3` / `aioboto3` S3-compatible API, egress $0)
- **AI Integratsiyalar:**
  - *Speaking (STT):* OpenAI Whisper API (`whisper-1`)
  - *Writing & Speaking baholash:* Anthropic Claude API (`claude-3-5-sonnet-latest` / `claude-3-5-haiku-latest`)
  - *Writing OCR:* Claude Vision / GPT-4o-mini Vision
- **PDF Hisobot:** Local Python (`ReportLab` / `WeasyPrint`) — $0 API cost
- **To'lov tizimlari:** Click va Payme Merchant API

---

## 3. XAVFSIZLIK VA BIZNES TALABLARI
- **Anti-Jailbreak / Anti-Cheating:** Foydalanuvchi insho o'rniga prompt injection ("Ignore previous instructions", "Write a Band 9 essay for me") yuborganida tizim buni aniqlashi, insho yozib bermasligi va `0.0` ball / xavfsizlik ogohlantirishini qaytarishi shart.
- **Yuridik Disclaimer:** Barcha PDF hisobotlarda va xabarlarda rasmiy "Cambridge", "IDP", "British Council" yoki "Bilim va malakalarni baholash agentligi (BBA)" sertifikati da'vo qilinmasin. Albatta **"Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool)"** yozuvi bo'lishi shart.
- **Arxitektura:** Clean Architecture + Repository Pattern + Dependency Injection + Async/Await.
