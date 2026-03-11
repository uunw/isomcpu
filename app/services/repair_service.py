from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from ..models.repair_request import RepairRequest
from ..models.technician import Technician
from ..models.repair_status_log import RepairStatusLog
from ..schemas.repair_request import RepairRequestCreate

# Define 13 status sequence (Added CANCELLED as a terminal state)
STATUS_SEQUENCE = [
    "PENDING_REPAIR",      # คำขอส่งซ่อม
    "PICKING_UP",          # กำลังไปรับเครื่อง
    "RECEIVED",            # รับเครื่องแล้ว
    "AT_SHOP",             # เครื่องถึงร้าน
    "WAITING_CHECK",       # รอเช็คปัญหา
    "DIAGNOSING",          # ตรวจเช็คปัญหา
    "QUOTED",              # ส่งใบเสนอราคา
    "PAID",                # จ่ายเงินแล้ว
    "REPAIRING",           # กำลังซ่อม
    "REPAIRED",            # ซ่อมเสร็จ
    "DELIVERING",          # กำลังส่งเครื่องกลับ
    "COMPLETED",           # ลูกค้ารับเครื่องแล้ว
    "CANCELLED"            # ยกเลิกการซ่อม
]

STATUS_DISPLAY = {
    "PENDING_REPAIR": "คำขอส่งซ่อม",
    "PICKING_UP": "กำลังไปรับเครื่อง",
    "RECEIVED": "รับเครื่องแล้ว",
    "AT_SHOP": "เครื่องถึงร้าน",
    "WAITING_CHECK": "รอเช็คปัญหา",
    "DIAGNOSING": "ตรวจเช็คปัญหา",
    "QUOTED": "ส่งใบเสนอราคา",
    "PAID": "จ่ายเงินแล้ว",
    "REPAIRING": "กำลังซ่อม",
    "REPAIRED": "ซ่อมเสร็จ",
    "DELIVERING": "กำลังส่งเครื่องกลับ",
    "COMPLETED": "ลูกค้ารับเครื่องแล้ว",
    "CANCELLED": "ยกเลิกการซ่อม"
}

def create_repair(repair: RepairRequestCreate, db: Session):
    best_tech = db.query(Technician).outerjoin(
        RepairRequest, Technician.id == RepairRequest.technicianID
    ).group_by(
        Technician.id
    ).order_by(
        func.count(RepairRequest.id).asc()
    ).first()

    new_repair = RepairRequest(
        **repair.model_dump(exclude={"technicianID", "status"}),
        technicianID=best_tech.id if best_tech else None,
        status="PENDING_REPAIR"
    )
    db.add(new_repair)
    db.flush()

    log = RepairStatusLog(
        repairRequestId=new_repair.id,
        status="PENDING_REPAIR",
        changedAt=datetime.utcnow()
    )
    db.add(log)
    
    db.commit()
    db.refresh(new_repair)
    return new_repair

def update_status(queue_id: str, new_status: str, db: Session, technician_id: int = None):
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")

    current_status = repair.status
    if current_status not in STATUS_SEQUENCE or new_status not in STATUS_SEQUENCE:
        raise HTTPException(status_code=400, detail="สถานะไม่ถูกต้อง")
    
    # Special Rule: Cancellation can happen from almost anywhere before repair starts
    if new_status == "CANCELLED":
        pass # Allow cancellation
    else:
        current_idx = STATUS_SEQUENCE.index(current_status)
        new_idx = STATUS_SEQUENCE.index(new_status)

        if new_idx <= current_idx:
            raise HTTPException(status_code=400, detail="ไม่สามารถย้อนสถานะได้")
        
        if new_idx != current_idx + 1:
            raise HTTPException(status_code=400, detail=f"ต้องขยับสถานะตามลำดับ (สถานะถัดไปคือ {STATUS_DISPLAY.get(STATUS_SEQUENCE[current_idx+1])})")

    repair.status = new_status
    repair.updatedAt = datetime.utcnow()
    
    if new_status in ["COMPLETED", "CANCELLED"]:
        repair.completedAt = datetime.utcnow()

    log = RepairStatusLog(
        repairRequestId=repair.id,
        status=new_status,
        changedAt=datetime.utcnow(),
        changedBy=technician_id
    )
    db.add(log)
    db.commit()
    db.refresh(repair)
    return repair

def get_repair_by_lineid(lineId: str, db: Session):
    repair_data = db.query(RepairRequest).filter(
            RepairRequest.lineUserId == lineId, 
            RepairRequest.status != "COMPLETED",
            RepairRequest.status != "CANCELLED"
    ).first()
    if not repair_data:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")
    return repair_data
