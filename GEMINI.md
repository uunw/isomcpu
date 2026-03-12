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
  - **LIFF (Mobile):** Rendered via `liff.html` using Alpine.js. Includes real-time auto-polling (3s) and 12-stage tracking.
  - **Technician Dashboard:** Single Page Application (SPA) served via `tech.html` with Alpine.js, Chart.js for analytics, and Jinja2 components.

---

## 2. Core Architecture

### Web Layer (`app/routers/`)
- `liff.py`: Handles customer-facing LIFF views.
- `tech.py`: Template router for the Technician SPA Dashboard.
- `tech_api.py`: Backend API for technician operations (Auth, Profile, Repairs, Media, Quotations).
- `line_webhook.py`: Processes incoming LINE Messaging API events.
- `repairs.py`: Unified repair and quotation management for customers.

### Service Layer (`app/services/`)
- `line_service.py`: LINE interaction logic using external JSON templates (`line_templates.json`).
- `repair_service.py`: Core repair lifecycle management, strict status transitions, and dashboard statistics.
- `media_service.py`: Image (WebP 80%) and Video (MP4 H.264) compression service.
- `quotation_service.py`: Business logic for creating and managing quotations.

### Template Layer (`app/templates/`)
- `liff.html` & `tech.html`: Master templates.
- `tech/`: Component-based views (`mywork`, `overview`, `queue_all`, `tech_manage`, `profile`).
- `liff/`: Customer views with refined capsule-style UI.

---

## 3. Key Features & Workflows

### Status State Machine (Strict 12-Stage Lifecycle)
1. `PENDING_REPAIR` -> 2. `PICKING_UP` -> 3. `RECEIVED` -> 4. `AT_SHOP` -> 5. `WAITING_CHECK` -> 6. `DIAGNOSING` -> 7. `QUOTED` -> 8. `PAID` -> 9. `REPAIRING` -> 10. `REPAIRED` -> 11. `DELIVERING` -> 12. `COMPLETED`

### Technician Dashboard (SPA)
- **Overview:** Real-time stats and repair trends via Chart.js.
- **My Work:** Task management, media uploads, and quotation creation.
- **Queue All:** Global visibility with technician filtering and manual assignment override.
- **Profile:** Self-service profile updates and secure password management.
- **Notifications:** Direct-to-LINE customer messaging for issue reporting.

### Customer LIFF Experience
- **Real-time Tracking:** 3-second auto-polling ensures status and date updates are visible instantly.
- **Quotation/Payment:** Integrated QR code payment (PromptPay) and confirmation flow.
- **Receipt Confirmation:** Customers formally end the process by confirming device receipt, triggering automated thank-you messages.

---

## 4. Operational Mandates

- **UI Standards:** **SweetAlert2** for all feedback. **Chart.js** for analytics. **Capsule-style** data rows.
- **Media Handling:** Server-side compression for WebP images and MP4 videos.
- **Dev Support:** All API calls include `ngrok-skip-browser-warning: true`.
- **Navigation:** Full SPA routing with Popstate support for Browser Back/Forward buttons.

---

## 5. Development Guidelines

- **Run Locally:** `uv run uvicorn app.main:app --reload`
- **Deploy:** `./deploy.sh` (Automated packaging, upload, and building).
- **Schema Fix:** `uv run python scripts/db_fix.py`
