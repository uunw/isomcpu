"""
Router for repair requests and quotations tracking for customers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.repair_request import RepairRequest
from ..models.quotation import Quotation
from ..schemas.repair_request import RepairRequestCreate
from ..schemas.quotation import QuotationWithItemsResponse
from ..services.repair_service import create_repair, get_repair_by_lineid
from ..services.line_service import push_message

router = APIRouter()


@router.post("/create", response_model=RepairRequestCreate)
def create_repair_request_endpoint(repair_in: RepairRequestCreate, db: Session = Depends(get_db)):
    """
    Create a new repair request and notify user via LINE.
    """
    repair = create_repair(repair_in, db)
    message = (
        "ทางร้านได้รับข้อมูลการซ่อมเรียบร้อยแล้ว\n"
        f"เลขคิวของคุณคือ {repair.queueId}\n"
        "สามารถ ดูสถานะงานได้ที่ปุ่มด้านล่าง ได้เลยครับ"
    )
    push_message(repair.lineUserId, message)
    return repair


@router.get("/track")
def get_repair_tracking(line_user_id: str, db: Session = Depends(get_db)):
    """
    Track the latest active repair request for a LINE user.
    """
    repair = (
        db.query(RepairRequest)
        .filter(RepairRequest.lineUserId == line_user_id)
        .filter(RepairRequest.status != "COMPLETED")
        .order_by(RepairRequest.createdAt.desc())
        .options(joinedload(RepairRequest.technician))
        .first()
    )
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลแจ้งซ่อม")
    return repair


@router.get("/all")
def list_all_repairs(db: Session = Depends(get_db)):
    """
    List all repair requests in the system.
    """
    return db.query(RepairRequest).options(joinedload(RepairRequest.technician)).all()


@router.get("/quotation", response_model=QuotationWithItemsResponse)
def get_repair_quotation(repair_id: int, db: Session = Depends(get_db)):
    """
    Get the quotation details for a specific repair request.
    """
    quotation = (
        db.query(Quotation)
        .options(joinedload(Quotation.items))
        .filter(Quotation.repairId == repair_id)
        .first()
    )
    if not quotation:
        raise HTTPException(status_code=404, detail="ไม่พบใบเสนอราคา")
    return quotation


@router.put("/update-status-customer")
def update_status_customer(queue_id: str, new_status: str, new_address: str = None, db: Session = Depends(get_db)):
    """
    Simplified status update for customer actions (Confirm/Pay/Cancel).
    """
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล")
    
    # Validation: Only allow specific statuses for customer
    allowed = ["WAITING_FOR_PAYMENT", "PAID", "CANCELLED"]
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="ไม่อนุญาตให้เปลี่ยนเป็นสถานะนี้")

    repair.status = new_status
    if new_address:
        repair.address = new_address
        
    db.commit()
    db.refresh(repair)
    return repair
