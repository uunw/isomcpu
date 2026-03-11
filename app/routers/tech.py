"""
Template routes for Technician dashboard views.
"""
import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Setup Jinja2 Templates
current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

@router.get("/tech")
async def tech_root(request: Request):
    return templates.TemplateResponse("tech.html", {"request": request, "view": "mywork"})

@router.get("/tech/{path}")
async def tech_dashboard(request: Request, path: str):
    # Ensure the path is valid or default to mywork
    valid_views = ["mywork", "overview", "queue-all", "tech-manage"]
    if path not in valid_views:
        path = "mywork"
    return templates.TemplateResponse("tech.html", {"request": request, "view": path})
