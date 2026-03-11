# GEMINI.md - ISOMCOM Codebase Index

This document provides a comprehensive index and architectural overview of the ISOMCOM project, a repair management system integrated with the LINE Messaging API.

---

## 1. Project Overview

- **Purpose:** A backend system for managing device repair requests, quotations, and payments, interacting with users through a LINE chatbot.
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database:** PostgreSQL (Hosted on Neon)
- **Integration:** [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)
- **Frontend Integration:** 
  - **LIFF (Mobile):** Rendered via `liff.html` using Alpine.js.
  - **Technician Dashboard:** Single Page Application (SPA) served via `tech.html` with Alpine.js and Jinja2 components. Integrated logic in `scripts.html`.

---

## 2. Core Architecture

### Web Layer (`app/routers/`)
- `liff.py`: Handles customer-facing LIFF views.
- `tech.py`: Template router for the Technician SPA Dashboard.
- `tech_api.py`: Backend API for technician operations (mounted at `/api/tech`).
- `line_webhook.py`: Processes incoming LINE Messaging API events.

### Service Layer (`app/services/`)
- `line_service.py`: LINE interaction logic, Flex Messages, and troubleshooting advice.
- `repair_service.py`: Core repair lifecycle management and strict status transition logic.

### Template Layer (`app/templates/`)
- `liff.html` & `tech.html`: Master templates.
- `tech/`: Component-based views (`view_mywork.html`, `view_overview.html`, `view_queue_all.html`, `view_tech_manage.html`).
- `tech/scripts.html`: Centralized Alpine.js logic for the Technician SPA.

### Frontend Assets (`frontend/`)
- `frontend/liff/`: Static assets for customers.
- `frontend/tech/`: Static assets for technicians (mounted at `/tech-assets`).

---

## 3. Status State Machine (Strict 12-Stage Lifecycle)

The system enforces a granular 12-stage repair lifecycle using English Uppercase keys:
1. `PENDING_REPAIR` -> 2. `PICKING_UP` -> 3. `RECEIVED` -> 4. `AT_SHOP` -> 5. `WAITING_CHECK` -> 6. `DIAGNOSING` -> 7. `QUOTED` -> 8. `PAID` -> 9. `REPAIRING` -> 10. `REPAIRED` -> 11. `DELIVERING` -> 12. `COMPLETED`

- **Rules:** Statuses must be updated sequentially. The `PAID` status requires customer confirmation (simulated in dev).
- **History:** Every status change is logged in `repair_status_logs` with timestamps and technician attribution.

---

## 4. Operational Mandates

- **UI Standards:** **SweetAlert2** for all user feedback. **Chevron-style** status buttons in the Tech Dashboard.
- **Media Handling:** Images are auto-compressed to **WebP (80% quality)** using Pillow. Videos are compressed to **MP4 (H.264, CRF 28)** using FFmpeg.
- **Dev Support:** All API calls from the frontend include `ngrok-skip-browser-warning: true`.
- **Navigation:** Supports Query String (`?id=...`) for direct linking to repair jobs in the My Work view.

---

## 5. Development Guidelines

- **Run Locally:** `uv run uvicorn app.main:app --reload`
- **Schema Fix:** `uv run python scripts/db_fix.py`
- **Migration:** `uv run python scripts/migrate_status.py`
