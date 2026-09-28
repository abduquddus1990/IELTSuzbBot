---
name: fastapi-aiogram-clean-arch
description: >-
  Clean Architecture, Repository Pattern, and Async SQLAlchemy 2.0 guidelines for
  building scalable FastAPI + aiogram 3 + PostgreSQL + Cloudflare R2 applications.
  Activate this skill when creating models, repositories, services, API endpoints, or bot handlers.
---

# FastAPI + aiogram 3 Clean Architecture Skill

## 1. Layered Architecture Rules
- **`app/models/`**: Pure SQLAlchemy 2.0 declarative models (`Mapped`, `mapped_column`). No business logic.
- **`app/schemas/`**: Pure Pydantic v2 schemas (`BaseModel`, `ConfigDict(from_attributes=True)`).
- **`app/repositories/`**: Database CRUD operations encapsulating `AsyncSession`. Services must call repositories instead of writing raw SQL/ORM queries directly.
- **`app/services/`**: Core business logic, AI integrations (Claude, Whisper, OCR), PDF generation (ReportLab), R2 storage, and payment processing (Click/Payme).
- **`app/api/`**: FastAPI routers, dependencies, and webhook endpoints (Telegram webhook, Click/Payme callbacks, Mini App REST API).
- **`app/bot/`**: `aiogram 3.x` routers, FSM states, keyboards, and middlewares.

## 2. Cost-Optimization Rules
- **Listening & Reading:** Must use 100% deterministic Python scoring (`$0.00` AI token cost).
- **Database Pooling:** Use `asyncpg` compatible connection pooling suitable for Neon / Supabase serverless PostgreSQL (`pool_pre_ping=True`).
- **Cloudflare R2:** Store voice `.ogg` and essay images in R2 with lifecycle policies or compressed uploads.
