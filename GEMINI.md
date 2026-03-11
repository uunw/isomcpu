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
  - **LIFF (Mobile):** Rendered via `liff.html` using Alpine.js. Includes high-fidelity tracking with 12-stage timeline.
  - **Technician Dashboard:** Single Page Application (SPA) served via `tech.html` with Alpine.js and Jinja2 components. Centralized logic in `scripts.html`.

---

## 2. Core Architecture

### Web Layer (`app/routers/`)
- `liff.py`: Handles customer-facing LIFF views.
- `tech.py`: Template router for the Technician SPA Dashboard.
- `tech_api.py`: Backend API for technician operations (mounted at `/api/tech`).
- `line_webhook.py`: Processes incoming LINE Messaging API events.
- `repairs.py`: Unified repair and quotation management for customers.

### Service Layer (`app/services/`)
- `line_service.py`: LINE interaction logic using external JSON templates (`line_templates.json`).
- `repair_service.py`: Core repair lifecycle management and strict status transition logic.
- `media_service.py`: Image (WebP 80%) and Video (MP4 H.264) compression service.
- `quotation_service.py`: Business logic for creating and managing quotations.

### Template Layer (`app/templates/`)
- `liff.html` & `tech.html`: Master templates.
- `tech/`: Component-based views (`view_mywork.html`, `view_overview.html`, `view_queue_all.html`, `view_tech_manage.html`).
- `liff/`: Customer views with refined capsule-style UI.

---

## 3. Status State Machine (Strict 12-Stage Lifecycle)

The system enforces a granular 12-stage repair lifecycle:
1. `PENDING_REPAIR` -> 2. `PICKING_UP` -> 3. `RECEIVED` -> 4. `AT_SHOP` -> 5. `WAITING_CHECK` -> 6. `DIAGNOSING` -> 7. `QUOTED` -> 8. `PAID` -> 9. `REPAIRING` -> 10. `REPAIRED` -> 11. `DELIVERING` -> 12. `COMPLETED`

- **Manual Override:** Global queue view allows manual technician assignment for unassigned tasks.
- **Cancellation:** Supports `CANCELLED` status with specialized return flow and address selection.

---

## 4. Operational Mandates

- **UI Standards:** **SweetAlert2** for all user feedback. **Chevron-style** status buttons. **Capsule-style** data rows in LIFF.
- **Media Handling:** Automated server-side compression for images and videos.
- **Dev Support:** All API calls include `ngrok-skip-browser-warning: true`.
- **Navigation:** Full SPA routing support with Browser Back/Forward compatibility and Deep Linking (`?id=...`).

---

## 5. Development Guidelines

- **Run Locally:** `uv run uvicorn app.main:app --reload`
- **Deploy:** `./deploy.sh` (Automated packaging, upload, build, and migration).
- **Schema Fix:** `uv run python scripts/db_fix.py`
