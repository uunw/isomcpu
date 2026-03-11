"""
Main entry point for the ISOMCOM Repair System API.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import os
from .routers import line_webhook, repairs, tech_api, payment, liff, tech
from .database import engine, Base
from .config import FRONTEND_URL

# สั่งสร้างตารางทั้งหมดใน Neon (ถ้ายังไม่มี)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LINE Repair System", 
    docs_url="/api/docs", 
    openapi_url="/api/openapi.json"
)

# ปรับปรุงความปลอดภัยของ CORS
origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware สำหรับ Redirect .html
@app.middleware("http")
async def redirect_html_extension(request: Request, call_next):
    path = request.url.path
    if path.endswith(".html") and path != "/":
        new_path = path[:-5]
        # พิเศษสำหรับ index.html -> /
        if new_path == "/index":
            new_path = "/"
        return RedirectResponse(url=new_path, status_code=307)
    response = await call_next(request)
    return response

# --- API Routers (Prefix with /api) ---
app.include_router(line_webhook.router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(repairs.router, prefix="/api/repairs", tags=["Repairs"])
app.include_router(tech_api.router, prefix="/api/tech", tags=["Technician API"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])

# --- Frontend Routers (LIFF & Tech Templates) ---
app.include_router(liff.router, tags=["LIFF"])
app.include_router(tech.router, tags=["Technician Dashboard"])

# Ensure uploads directory exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- Static File Mounting ---

# 1. Technician Dashboard Assets (Static) at /tech-assets
app.mount("/tech-assets", StaticFiles(directory="frontend/tech"), name="tech_assets")

# 2. Static assets for LIFF (JS, CSS, Img)
app.mount("/static", StaticFiles(directory="frontend/liff"), name="liff_static")

# 3. Uploaded Media
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
