# IELTS & CEFR Mock AI

Bepul IELTS Academic va O'zbekiston Multilevel (CEFR) sinov imtihonlari platformasi. Interfeys real kompyuterda topshiriladigan (computer-delivered) imtihon ko'rinishida, AI esa natijani darhol baholaydi.

- **Mini App / brauzer** (`/webapp/`) — to'liq imtihon: Listening, Reading, Writing va Speaking, oxirida PDF hisobot. Telefonda ham, kompyuterda ham ishlaydi.
- **Telegram bot** — chatning o'zida Writing (matn yoki daftar rasmi) va Speaking (ovozli xabarlar) mashqi.

> Mustaqil AI baholash va tayyorgarlik vositasi (Unofficial Mock Assessment Tool). Rasmiy IELTS, Cambridge, IDP, British Council yoki BBA sertifikati emas.

## Imtihon qanday o'tadi

| Bo'lim | Nima bor |
|---|---|
| Listening | Har bir qism (IELTS: 4 ta, CEFR: 6 ta) audiosi **bir marta** eshittiriladi va keyingi qismga avtomatik o'tadi. Pauza ham, orqaga qaytarish ham yo'q. Barcha variantlar ekranda ochiq turadi. Audio tugagach javoblarni tekshirish uchun 2 daqiqa beriladi. |
| Reading | Ekran ikkiga bo'lingan: chapda matn, o'ngda faqat shu matnga tegishli savollar (chegarasini sichqoncha bilan surish mumkin). Shrift kattaligini o'zgartirish va savolni ⚑ belgilab qo'yish mumkin. Vaqt — 60 daqiqa. |
| Writing | Chapda topshiriq va **Task 1 grafigi**, o'ngda javob maydoni va so'zlar hisoblagichi. Daftarga qo'lda yozilgan javob rasmini yuklasa ham bo'ladi (OCR). Vaqt — 60 daqiqa. |
| Speaking | Examiner savollarni **birma-bir** beradi va ovoz chiqarib o'qiydi. Part 1 — 3 mavzu bo'yicha ~10 savol. Part 2 — cue card, 1 daqiqa tayyorgarlik, keyin 2 daqiqagacha gapiriladi. Part 3 — Part 2 mavzusiga bog'liq 5 ta savol. Javoblar mikrofon orqali yoziladi. |

Pastki panelda barcha savol raqamlari turadi: javob berilganlari ko'k rangda, belgilanganlari ⚑ bilan ko'rsatiladi. AI fikr-mulohazasi tanlangan tilda beriladi: O'zbekcha, Русский yoki English.

## Bepul rejim va limitlar

- Hamma narsa bepul. To'lov kodi (`payments.py`, `billing_and_admin.py`) o'chirib qo'yilgan, lekin keyinchalik kerak bo'lsa qayta yoqish mumkin.
- Kuniga **2 ta AI baholaydigan imtihon** (`DAILY_EXAM_LIMIT`) — to'liq mock, faqat Writing yoki faqat Speaking.
- Listening va Reading mashqi **cheksiz**, chunki ularga AI xarajati ketmaydi.
- AI ishlamay qolsa urinish limitdan hisoblanmaydi va nomzodga soxta ball berilmaydi (`ALLOW_DEMO_AI_FALLBACK=False`).
- Telegram foydalanuvchisi tasdiqlangan Telegram ID orqali, brauzer foydalanuvchisi esa qurilma ID'si va IP manzili orqali aniqlanadi.
- Limit hisoblagichlari `DATABASE_URL` (bepul Neon yoki Supabase) da saqlanadi. Baza ulanmagan bo'lsa, lokal faylda saqlanadi — u Render qayta ishga tushganda o'chib ketadi.

## Reklama (daromad)

| Joy | Tarmoq | Sozlama |
|---|---|---|
| Telegram Mini App — natija hisoblanayotgan paytda | [Adsgram](https://adsgram.ai) | `ADSGRAM_BLOCK_ID` |
| Brauzer versiyasi — bosh sahifa va natijalar sahifasi | Google AdSense | `ADSENSE_CLIENT_ID`, `ADSENSE_SLOT_ID` |

ID'lar kiritilmaguncha reklama ko'rinmaydi. Imtihon davomida reklama ataylab ko'rsatilmaydi.

## Ishga tushirish (lokal)

```bash
pip install -r requirements.txt
cp .env.example .env               # BOT_TOKEN va GEMINI_API_KEY ni kiriting
pytest                              # 83 ta test
uvicorn app.main:app --reload --port 8080
# brauzerda: http://localhost:8080/  (avtomatik /webapp/ ga o'tadi)
```

`RUN_BOT_POLLING_IN_WEB=true` bo'lsa, bot shu jarayonning ichida ishga tushadi. Lokal kompyuterda buni yoqmang, chunki bir vaqtda faqat bitta polling ishlay oladi va Render'dagi bot bilan to'qnashadi.

## Render'ga deploy

1. Render'da quyidagi environment variable'larni o'rnating (`render.yaml` ga qarang): `APP_ENV=production`, `DEBUG=false`, `SECRET_KEY` (uzun tasodifiy qator, **o'zgartirmang** — PDF havolalari shu kalit bilan imzolanadi), `BOT_TOKEN`, `GEMINI_API_KEY`, `DATABASE_URL`, `ADMIN_TELEGRAM_IDS`.
2. Bepul PostgreSQL oling: [neon.tech](https://neon.tech) → *Connection string* (`postgresql://...?sslmode=require`) ni `DATABASE_URL` ga qo'ying. Kerakli jadval avtomatik yaratiladi.
3. Render'ning bepul tarifi 15 daqiqa so'rov bo'lmasa "uxlab qoladi", shunda bot ham to'xtaydi. [cron-job.org](https://cron-job.org) da har 10 daqiqada `https://<app>.onrender.com/api/v1/health` manziliga so'rov yuboradigan bepul vazifa qo'shing.

PDF hisobotlar disk o'chib ketishiga chidamli: yuklab olish havolasida imzolangan token bor, server qayta ishga tushsa ham PDF shu tokendan qayta yaratiladi. Telegram foydalanuvchisiga PDF bot orqali chatga ham yuboriladi.

## Kontent

- `app/services/content/ielts_set1.py`, `cefr_set1.py` — Listening (audio skriptlari bilan) va Reading matnlari, savollar, javob kalitlari. Skriptlar va kalitlar mijozga yuborilmaydi.
- IELTS to'plami haqiqiy Cambridge IELTS Academic darajasiga moslab **original** yozilgan: har bir Reading matni ~870–890 so'z, savollar parafraz qilingan, Listening'da chalg'ituvchi javoblar bor. Mualliflik huquqi bilan himoyalangan kitob matnlarini (masalan, Cambridge IELTS seriyasi) ilovaga ko'chirmang.
- Qo'llab-quvvatlanadigan savol turlari (`app/services/content/builders.py`): `gap` (eslatma/gap/summary, `table` bilan — jadval), `mcq`, `matching` (abzats, shaxs, phrase bank A–J, xarita), `multi` ("Choose TWO letters", tartibsiz baholanadi), `tfng`, `ynng`.
- `app/services/content/writing_charts.py` — 10 ta Task 1 grafigining ma'lumotlari. Ular `app/services/chart_renderer.py` orqali PNG'ga chiziladi va AI'ga ham uzatiladi, shunda AI nomzod keltirgan raqamlarni tekshira oladi.
- `app/services/content/speaking_bank.py` — Speaking savollari banki.
- Audio yaratish: `pip install edge-tts`, ffmpeg o'rnatilgan bo'lishi kerak, so'ng `python -m tools.generate_listening_audio`. Yangi to'plam qo'shish uchun xuddi shu tuzilishda fayl yarating va uni `SETS` ga qo'shing.

## Bot buyruqlari

`/start` — menyu, `/mock` — imtihon tanlash, `/help` — yordam, `/stats` — bugungi statistika (faqat `ADMIN_TELEGRAM_IDS` dagilar uchun).
