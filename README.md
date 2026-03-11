# ISOMCOM - LINE Repair Management System

A robust repair management backend built with FastAPI, featuring a unified LIFF experience for customers and a dedicated dashboard for technicians.

## 🚀 Key Features

- **Modular Frontend Architecture:**
  - **Single-Template LIFF:** All views (Repair, Track, Queue) are powered by a unified `liff.html` with Alpine.js reactivity.
  - **Extensionless URLs:** Clean routing (e.g., `/track`, `/tech`).
  - **Technician Portal (`/tech/`):** Specialized interface for managing repairs and quotations.
- **Interactive Chatbot:**
  - **Troubleshooting System:** Guided advice for common device issues with instant repair links.
  - **Status Notifications:** Real-time LINE Flex Message updates when repair status changes.
- **Hardened Backend:**
  - **FastAPI + SQLAlchemy 2.0:** High-performance API with resilient DB pooling.
  - **Clean Code:** Modularized routers and services following PEP 8.

## 📂 Project Structure

```text
ISOMCOM/
├── app/                 # Backend (FastAPI)
│   ├── templates/       # Modular LIFF Templates (Jinja2 + Alpine.js)
│   ├── routers/         # API & Template Routers
│   ├── services/        # Business Logic & LINE Integration
│   └── models/          # SQLAlchemy Models
├── frontend/            # Static Assets
│   ├── liff/            # LIFF CSS & Images
│   └── tech/            # Technician Dashboard Static Files

├── docs/                # API Documentation
└── pyproject.toml       # Dependency Management (uv)
```

## ⚙️ Deployment

- **Production URL:** [https://isomcpu.duckdns.org/](https://isomcpu.duckdns.org/)
- **Tech Portal:** [https://isomcpu.duckdns.org/tech/](https://isomcpu.duckdns.org/tech/)
- **API Docs:** [https://isomcpu.duckdns.org/api/docs](https://isomcpu.duckdns.org/api/docs)

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.14+)
- **Database:** PostgreSQL (Neon.tech)
- **Frontend:** Jinja2, Alpine.js, Bootstrap 5
- **Proxy:** Traefik v3.6 with Let's Encrypt SSL

## 💻 Development

This project uses `uv` for dependency management.

### 1. Setup Environment
```bash
# Install dependencies
uv sync
```

### 2. Run Locally
```bash
# Start FastAPI server with auto-reload
uv run uvicorn app.main:app --reload
```

### 3. Database Management
If you've updated the models or need to sync statuses:
```bash
# Fix schema (add missing columns/tables)
uv run python scripts/db_fix.py

# Migrate existing data to new status system
uv run python scripts/migrate_status.py
```

### 4. Docker (Production Simulation)
```bash
docker compose up --build
```

## ⚙️ Deployment

This project includes an automated deployment script for the App Server.

### To Deploy to Production:
```bash
# Ensure you have SSH access to 192.168.88.233
./deploy.sh
```
This script will:
1. Pack the project (excluding unnecessary files).
2. Upload the archive to the server.
3. Build and restart Docker containers on the server.
4. Run database schema fixes and data migrations automatically.

## 📄 License
This project is for internal use by ISOMCOM.
