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
from ..services.repair_service import create_repair, update_status as svc_update_status
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
    Simplified status update for customer actions (Pay/Cancel/Complete).
    """
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูล")

    # Validation: Only allow specific statuses for customer
    allowed = ["PAID", "CANCELLED", "COMPLETED"]
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="ไม่อนุญาตให้เปลี่ยนเป็นสถานะนี้โดยลูกค้า")

    # Update address if provided (for CANCELLED case)
    if new_address:
        repair.address = new_address
        db.commit()

    # Use service to handle status transition and logging
    try:
        updated_repair = svc_update_status(queue_id, new_status, db)
        
        # ส่งแจ้งเตือนกลับไปที่ LINE ลูกค้า
        if updated_repair.lineUserId:
            from ..services.line_service import push_update_notification, push_message
            try:
                push_update_notification(updated_repair.lineUserId, updated_repair.queueId, new_status)
                
                # ถ้ากดรับเครื่องสำเร็จ ให้ส่งข้อความขอบคุณพิเศษ
                if new_status == "COMPLETED":
                    thanks_msg = (
                        "🙏 ขอบคุณที่ไว้วางใจใช้บริการ I SOM CPU ครับ!\n\n"
                        "เครื่องของคุณได้รับการซ่อมแซมและส่งคืนเรียบร้อยแล้ว "
                        "หากพบปัญหาการใช้งานเพิ่มเติม สามารถติดต่อสอบถามทางร้านได้ตลอดเวลาครับ"
                    )
                    push_message(updated_repair.lineUserId, thanks_msg)
            except Exception:
                pass

        return updated_repair
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
