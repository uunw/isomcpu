"""
Service layer for handling repair requests and status transitions.
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException

from ..models.repair_request import RepairRequest
from ..models.technician import Technician
from ..models.repair_status_log import RepairStatusLog
from ..schemas.repair_request import RepairRequestCreate

class RepairStatus(str, Enum):
    PENDING_REPAIR = "PENDING_REPAIR"
    PICKING_UP = "PICKING_UP"
    RECEIVED = "RECEIVED"
    AT_SHOP = "AT_SHOP"
    WAITING_CHECK = "WAITING_CHECK"
    DIAGNOSING = "DIAGNOSING"
    QUOTED = "QUOTED"
    PAID = "PAID"
    REPAIRING = "REPAIRING"
    REPAIRED = "REPAIRED"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# Define Groups for Dashboard
TODO_STATUSES = [RepairStatus.PENDING_REPAIR, RepairStatus.PICKING_UP, RepairStatus.RECEIVED, RepairStatus.AT_SHOP]
WAITING_STATUSES = [RepairStatus.WAITING_CHECK, RepairStatus.DIAGNOSING, RepairStatus.QUOTED]
DONE_STATUSES = [RepairStatus.PAID, RepairStatus.REPAIRING, RepairStatus.REPAIRED, RepairStatus.DELIVERING, RepairStatus.COMPLETED]

# Strict Sequence
STATUS_SEQUENCE: List[RepairStatus] = [
    RepairStatus.PENDING_REPAIR, RepairStatus.PICKING_UP, RepairStatus.RECEIVED, RepairStatus.AT_SHOP,
    RepairStatus.WAITING_CHECK, RepairStatus.DIAGNOSING, RepairStatus.QUOTED, RepairStatus.PAID,
    RepairStatus.REPAIRING, RepairStatus.REPAIRED, RepairStatus.DELIVERING, RepairStatus.COMPLETED
]

STATUS_DISPLAY: Dict[RepairStatus, str] = {
    RepairStatus.PENDING_REPAIR: "คำขอส่งซ่อม",
    RepairStatus.PICKING_UP: "กำลังไปรับเครื่อง",
    RepairStatus.RECEIVED: "รับเครื่องแล้ว",
    RepairStatus.AT_SHOP: "เครื่องถึงร้าน",
    RepairStatus.WAITING_CHECK: "รอเช็คปัญหา",
    RepairStatus.DIAGNOSING: "ตรวจเช็คปัญหา",
    RepairStatus.QUOTED: "ส่งใบเสนอราคา",
    RepairStatus.PAID: "จ่ายเงินแล้ว",
    RepairStatus.REPAIRING: "กำลังซ่อม",
    RepairStatus.REPAIRED: "ซ่อมเสร็จ",
    RepairStatus.DELIVERING: "กำลังส่งเครื่องกลับ",
    RepairStatus.COMPLETED: "ลูกค้ารับเครื่องแล้ว",
    RepairStatus.CANCELLED: "ยกเลิกการซ่อม"
}

def create_repair(repair: RepairRequestCreate, db: Session) -> RepairRequest:
    best_tech = db.query(Technician).outerjoin(
        RepairRequest, Technician.id == RepairRequest.technicianID
    ).group_by(Technician.id).order_by(func.count(RepairRequest.id).asc()).first()

    new_repair = RepairRequest(
        **repair.model_dump(exclude={"technicianID", "status"}),
        technicianID=best_tech.id if best_tech else None,
        status=RepairStatus.PENDING_REPAIR
    )
    db.add(new_repair)
    db.flush()

    log = RepairStatusLog(repairRequestId=new_repair.id, status=RepairStatus.PENDING_REPAIR, changedAt=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(new_repair)
    return new_repair

def update_status(queue_id: str, new_status: str, db: Session, technician_id: int = None) -> RepairRequest:
    repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
    if not repair: raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")

    try:
        new_status_enum = RepairStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="สถานะไม่ถูกต้อง")

    current_status = RepairStatus(repair.status)
    if new_status_enum != RepairStatus.CANCELLED:
        if current_status in STATUS_SEQUENCE:
            current_idx = STATUS_SEQUENCE.index(current_status)
            new_idx = STATUS_SEQUENCE.index(new_status_enum)
            if new_idx <= current_idx: raise HTTPException(status_code=400, detail="ไม่สามารถย้อนสถานะได้")
            if new_idx != current_idx + 1:
                raise HTTPException(status_code=400, detail=f"ต้องขยับสถานะตามลำดับ (ถัดไปคือ {STATUS_DISPLAY.get(STATUS_SEQUENCE[current_idx+1])})")

    repair.status = new_status_enum
    repair.updatedAt = datetime.utcnow()
    if new_status_enum in [RepairStatus.COMPLETED, RepairStatus.CANCELLED]:
        repair.completedAt = datetime.utcnow()

    log = RepairStatusLog(repairRequestId=repair.id, status=new_status_enum, changedAt=datetime.utcnow(), changedBy=technician_id)
    db.add(log)
    db.commit()
    db.refresh(repair)
    return repair

def get_repair_by_lineid(lineId: str, db: Session) -> RepairRequest:
    repair_data = db.query(RepairRequest).filter(
            RepairRequest.lineUserId == lineId, 
            RepairRequest.status != RepairStatus.COMPLETED,
            RepairRequest.status != RepairStatus.CANCELLED
    ).first()
    if not repair_data: raise HTTPException(status_code=404, detail="ไม่พบข้อมูลการซ่อม")
    return repair_data

def get_dashboard_summary(db: Session, tech_id: int) -> Dict[str, Any]:
    """
    Fetch global stats, personal stats, and recent activities for the dashboard.
    """
    all_repairs = db.query(RepairRequest).all()
    
    def calc_stats(repairs_list):
        return {
            "total": len(repairs_list),
            "todo": len([r for r in repairs_list if r.status in TODO_STATUSES]),
            "waiting": len([r for r in repairs_list if r.status in WAITING_STATUSES]),
            "done": len([r for r in repairs_list if r.status in DONE_STATUSES])
        }

    global_stats = calc_stats(all_repairs)
    personal_stats = calc_stats([r for r in all_repairs if r.technicianID == tech_id])

    # Fetch recent activities (Last 15 logs)
    logs = db.query(RepairStatusLog).options(
        joinedload(RepairStatusLog.repairRequest)
    ).order_by(RepairStatusLog.changedAt.desc()).limit(15).all()

    activities = []
    for log in logs:
        if not log.repairRequest: continue
        activities.append({
            "timestamp": log.changedAt.isoformat(),
            "queueId": log.repairRequest.queueId,
            "customerName": log.repairRequest.fullName or "ลูกค้า",
            "status": log.status,
            "problem": log.repairRequest.problemType
        })

    return {
        "global": global_stats,
        "personal": personal_stats,
        "activities": activities
    }
