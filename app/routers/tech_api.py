"""
Technician router for managing technicians, repairs, and quotations.
"""
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_db
from ..models.technician import Technician
from ..models.repair_request import RepairRequest
from ..models.quotation import Quotation
from ..models.repair_media import RepairMedia
from ..schemas.technician import TechnicianResponse, TechnicianCreate, TechnicianUpdate, PasswordChange
from ..schemas.quotation import QuotationCreate
from ..utils.auth import verify_password, create_access_token, get_password_hash
from ..services.line_service import push_update_notification
from ..services.repair_service import update_status, get_dashboard_summary
from ..services.media_service import save_repair_media
from ..services.quotation_service import create_repair_quotation
from ..dependencies import get_current_technician

router = APIRouter()

@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db), current_tech: Technician = Depends(get_current_technician)):
    """
    Get dashboard stats and activities.
    """
    return get_dashboard_summary(db, current_tech.id)


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
    return current_tech


@router.put("/me", response_model=TechnicianResponse)
def update_profile(
    obj_in: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Update current technician profile.
    """
    if obj_in.email:
        existing = db.query(Technician).filter(Technician.email == obj_in.email, Technician.id != current_tech.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานโดยช่างคนอื่นแล้ว")
        current_tech.email = obj_in.email
    
    if obj_in.displayName:
        current_tech.displayName = obj_in.displayName
    if obj_in.firstName:
        current_tech.firstName = obj_in.firstName
    if obj_in.lastName:
        current_tech.lastName = obj_in.lastName
    if obj_in.phoneNumber:
        current_tech.phoneNumber = obj_in.phoneNumber
        
    db.commit()
    db.refresh(current_tech)
    return current_tech


@router.put("/change-password")
def change_password(
    obj_in: PasswordChange,
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Change current technician password.
    """
    if not verify_password(obj_in.oldPassword, current_tech.password):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    
    current_tech.password = get_password_hash(obj_in.newPassword)
    db.commit()
    return {"message": "เปลี่ยนรหัสผ่านสำเร็จ"}


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


@router.put("/repair/assign")
def assign_repair(
    queue_id: str, 
    tech_id: int, 
    db: Session = Depends(get_db), 
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Manually assign a technician to a repair request.
    """
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")
    
    repair.technicianID = tech_id
    db.commit()
    db.refresh(repair)
    return {"message": "มอบหมายงานสำเร็จ", "technician": repair.technician.displayName}


@router.put("/repair/details")
def update_repair_details(
    queue_id: str,
    pickup_date: str = None,
    problem_detail: str = None,
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Update specific repair details like pickup date or problem notes.
    """
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")
    
    if pickup_date:
        repair.pickupDate = pickup_date
    if problem_detail:
        repair.problemDetail = problem_detail
        
    db.commit()
    return {"message": "อัปเดตข้อมูลสำเร็จ"}


@router.post("/repair/notify-customer")
def notify_customer(
    queue_id: str,
    message: str,
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Send a custom notification message to the customer via LINE.
    """
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair or not repair.lineUserId:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลลูกค้าหรือ LINE ID")
    
    from ..services.line_service import push_message
    full_msg = f"🔔 แจ้งเตือนจากร้าน (คิว {queue_id}):\n{message}"
    push_message(repair.lineUserId, full_msg)
    return {"message": "ส่งข้อความสำเร็จ"}


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
    Create a new quotation using the Quotation Service.
    """
    create_repair_quotation(db, obj_in)
    return {"message": "สร้างใบเสนอราคาสำเร็จ"}


@router.post("/repair/upload")
async def upload_repair_media(
    repair_id: int = Form(...),
    section: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_tech: Technician = Depends(get_current_technician)
):
    """
    Upload and process media using the Media Service.
    """
    return save_repair_media(db, repair_id, section, file)


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
