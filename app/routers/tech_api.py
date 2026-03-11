"""
Technician router for managing technicians, repairs, and quotations.
"""
import os
import shutil
import uuid
import subprocess
from jose import jwt, JWTError
from PIL import Image
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from ..config import JWT_SECRET_KEY
from ..database import get_db
from ..models.technician import Technician
from ..models.repair_request import RepairRequest
from ..models.quotation import Quotation
from ..models.quotation_item import QuotationItem
from ..models.repair_media import RepairMedia
from ..schemas.technician import TechnicianResponse, TechnicianCreate
from ..schemas.quotation import QuotationCreate
from ..utils.auth import verify_password, create_access_token, get_password_hash
from ..services.line_service import push_update_notification
from ..services.repair_service import update_status

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_technician(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated technician from the JWT token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token ไม่ถูกต้อง")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token หมดอายุหรือผิดพลาด") from exc

    tech = db.query(Technician).filter(Technician.email == email).first()
    if tech is None:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลช่าง")

    return tech


@router.get("/all", response_model=list[TechnicianResponse])
def list_all_technicians(db: Session = Depends(get_db), current_tech: Technician = Depends(get_current_technician)):
    """
    List all technicians in the system.
    """
    return db.query(Technician).all()


@router.get("/me")
def me(db: Session = Depends(get_db), current_tech: Technician = Depends(get_current_technician)):
    """
    Get current technician profile.
    """
    tech = db.query(Technician).filter(Technician.id == current_tech.id).first()
    return tech


@router.get("/info")
def get_technician_info(tech_id: int, db: Session = Depends(get_db)):
    """
    Get technician info by ID.
    """
    return db.query(Technician).filter(Technician.id == tech_id).first()


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate technician and return access token.
    """
    tech = db.query(Technician).filter(Technician.email == form_data.username).first()

    if not tech or not verify_password(form_data.password, tech.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email หรือ Password ไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": tech.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    """
    Log out technician (Frontend handles token removal).
    """
    return {"message": "ออกจากระบบสำเร็จ"}


@router.post("/register", response_model=TechnicianResponse)
def register_technician(tech_in: TechnicianCreate, db: Session = Depends(get_db)):
    """
    Register a new technician.
    """
    existing_tech = db.query(Technician).filter(Technician.email == tech_in.email).first()
    if existing_tech:
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกลงทะเบียนในระบบแล้ว")

    hashed_password = get_password_hash(tech_in.password)

    new_tech = Technician(
        email=tech_in.email,
        password=hashed_password,
        displayName=tech_in.displayName,
        firstName=tech_in.firstName,
        lastName=tech_in.lastName,
        phoneNumber=tech_in.phoneNumber,
    )

    db.add(new_tech)
    db.commit()
    db.refresh(new_tech)

    return new_tech


@router.get("/repairs")
def list_repairs(
    db: Session = Depends(get_db), current_tech: Technician = Depends(get_current_technician)
):
    """
    List all pending repairs assigned to the current technician.
    """
    repairs_list = (
        db.query(RepairRequest)
        .filter(RepairRequest.technicianID == current_tech.id, RepairRequest.status != "COMPLETED")
        .all()
    )
    return repairs_list


@router.put("/repair/update")
def update_repair(
    queue_id: str, 
    status_name: str, 
    db: Session = Depends(get_db), 
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Update repair status and notify user via LINE.
    """
    updated_repair = update_status(queue_id, status_name, db, technician_id=current_tech.id)
    if updated_repair.lineUserId:
        try:
            push_update_notification(updated_repair.lineUserId, updated_repair.queueId, status_name)
        except Exception:
            pass
    return updated_repair


@router.post("/quotation/create")
def create_quotation(obj_in: QuotationCreate, db: Session = Depends(get_db), current_tech: Technician = Depends(get_current_technician)):
    """
    Create a new quotation for a repair.
    """
    new_quotation = Quotation(
        repairId=obj_in.repairId,
        totalPrice=obj_in.totalPrice,
        technicianNote=obj_in.technicianNote,
        status="PendingConfirmation",
    )
    db.add(new_quotation)
    db.flush()

    for item in obj_in.items:
        new_item = QuotationItem(
            quotationId=new_quotation.id,
            productName=item.productName,
            quantity=item.quantity,
            price=item.price,
        )
        db.add(new_item)

    try:
        db.commit()
        db.refresh(new_quotation)
        return {"message": "สร้างใบเสนอราคาสำเร็จ", "quotation_id": new_quotation.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/repair/upload")
async def upload_repair_media(
    repair_id: int = Form(...),
    section: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Upload a media file (image/video) for a specific repair and section.
    Images are compressed to WebP (80% quality).
    Videos are compressed to MP4 using FFmpeg (CRF 28).
    """
    is_image = file.content_type.startswith("image")
    is_video = file.content_type.startswith("video")
    
    unique_id = str(uuid.uuid4())
    upload_dir = "uploads"
    
    if is_image:
        filename = f"{unique_id}.webp"
        file_path = os.path.join(upload_dir, filename)
        try:
            img = Image.open(file.file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(file_path, "WEBP", quality=80)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image compression failed: {str(e)}")
            
    elif is_video:
        filename = f"{unique_id}.mp4"
        file_path = os.path.join(upload_dir, filename)
        temp_input = os.path.join(upload_dir, f"temp_{unique_id}_{file.filename}")
        
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # -vcodec libx264: H.264
            # -crf 28: Good balance of size/quality
            # -preset faster: Faster encoding
            # -movflags +faststart: Web optimized
            cmd = [
                "ffmpeg", "-i", temp_input,
                "-vcodec", "libx264", "-crf", "28", "-preset", "faster",
                "-acodec", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                "-y", file_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if os.path.exists(file_path): os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Video compression failed: {e.stderr.decode()}")
        finally:
            if os.path.exists(temp_input):
                os.remove(temp_input)
    else:
        ext = file.filename.split(".")[-1]
        filename = f"{unique_id}.{ext}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    file_type = "image" if is_image else ("video" if is_video else "other")
    new_media = RepairMedia(
        repairId=repair_id,
        fileUrl=f"/uploads/{filename}",
        fileType=file_type,
        section=section
    )
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    return new_media


@router.get("/repair/{repair_id}/media")
def list_repair_media(
    repair_id: int,
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    List all media files for a specific repair.
    """
    return db.query(RepairMedia).filter(RepairMedia.repairId == repair_id).all()
