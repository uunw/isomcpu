"""
Migration script to update Thai status strings to English Uppercase in the database.
Run with: uv run python -m scripts.migrate_status
"""
import sys
import os
from datetime import datetime

# เพิ่ม Root Path เข้าไปใน sys.path เพื่อให้ import 'app' ได้
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SESSION_LOCAL
from app.models.repair_request import RepairRequest
from app.models.repair_status_log import RepairStatusLog

# Mapping จากภาษาไทยเดิม (รวมตัวแปรต่างๆ) เป็น English Uppercase
MIGRATION_MAP = {
    "คำขอส่งซ่อม": "PENDING_REPAIR",
    "ส่งคำขอซ่อม": "PENDING_REPAIR",
    "กำลังไปรับเครื่อง": "PICKING_UP",
    "รับเครื่องแล้ว": "RECEIVED",
    "เครื่องถึงร้าน": "RECEIVED",
    "รอเช็คปัญหา": "DIAGNOSING",
    "ตรวจเช็กปัญหา": "DIAGNOSING",
    "ตรวจเช็คปัญหา": "DIAGNOSING",
    "ส่งใบเสนอราคา": "QUOTED",
    "รอการจ่ายเงิน": "WAITING_FOR_PAYMENT",
    "จ่ายเงินแล้ว": "PAID",
    "กำลังซ่อม": "REPAIRING",
    "ซ่อมเสร็จ": "REPAIRED",
    "ซ่อมเสร็จสิ้น": "REPAIRED",
    "ซ่อมเสร็จแล้ว": "REPAIRED",
    "กำลังส่งเครื่องกลับ": "DELIVERING",
    "ลูกค้ารับเครื่องแล้ว": "COMPLETED",
    "ลูกค้ากดรับเครื่องแล้ว": "COMPLETED",
    "Complete": "COMPLETED"
}

def migrate():
    db = SESSION_LOCAL()
    try:
        print("🔍 Starting migration of repair statuses...")
        
        # 1. ดึงงานทั้งหมด
        repairs = db.query(RepairRequest).all()
        count = 0
        
        for repair in repairs:
            old_status = repair.status
            new_status = MIGRATION_MAP.get(old_status)
            
            if new_status:
                # Update status
                repair.status = new_status
                
                # ถ้าเป็นสถานะจบงาน ให้ใส่เวลา completedAt
                if new_status == "COMPLETED" and not repair.completedAt:
                    repair.completedAt = repair.updatedAt or datetime.utcnow()
                
                # 2. สร้าง Log เริ่มต้นถ้ายังไม่มี (เพื่อให้ History ไม่ว่าง)
                existing_log = db.query(RepairStatusLog).filter(
                    RepairStatusLog.repairRequestId == repair.id,
                    RepairStatusLog.status == new_status
                ).first()
                
                if not existing_log:
                    log = RepairStatusLog(
                        repairRequestId=repair.id,
                        status=new_status,
                        changedAt=repair.updatedAt or datetime.utcnow(),
                        note="Migration from Thai Status"
                    )
                    db.add(log)
                
                print(f"✅ Updated [{repair.queueId}]: '{old_status}' -> '{new_status}'")
                count += 1
            else:
                if old_status in MIGRATION_MAP.values():
                    print(f"⏩ Skip [{repair.queueId}]: Already migrated ('{old_status}')")
                else:
                    print(f"⚠️ Warning: Unknown status found in [{repair.queueId}]: '{old_status}'")

        db.commit()
        print(f"\n✨ Migration completed! Total {count} records updated.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
