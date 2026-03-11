"""
Template routes for LIFF frontend views.
"""
import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

# ตั้งค่า Jinja2 Templates
current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@router.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse("liff.html", {"request": request, "view": "index", "title": "แจ้งซ่อม"})

@router.get("/track")
async def read_track(request: Request):
    return templates.TemplateResponse("liff.html", {"request": request, "view": "track", "title": "ติดตามสถานะ"})

@router.get("/queue")
async def read_queue(request: Request):
    return templates.TemplateResponse("liff.html", {"request": request, "view": "queue", "title": "คิวงานปัจจุบัน"})

@router.get("/return")
async def read_return(request: Request):
    return templates.TemplateResponse("liff.html", {"request": request, "view": "return", "title": "นัดรับเครื่องคืน"})

@router.get("/notfound-track")
async def read_notfound(request: Request):
    return templates.TemplateResponse("liff.html", {"request": request, "view": "notfound", "title": "ไม่พบข้อมูล"})
