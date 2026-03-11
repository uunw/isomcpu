"""
Router for LINE Messaging API webhooks and customer registration.
"""
from fastapi import APIRouter, Request, Header, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.customer import Customer
from ..schemas.customer import CustomerCreate
from ..services.line_service import handle_event
from ..services.repair_service import get_repair_by_lineid

router = APIRouter(redirect_slashes=False)


@router.post("")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    """
    Webhook endpoint to receive events from the LINE Messaging API.
    """
    if x_line_signature is None:
        raise HTTPException(status_code=400, detail="Missing Signature")

    # ดึง body เป็น byte string เพื่อใช้ตรวจสอบ Signature
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        # ส่งทั้ง body และ signature ไปให้ service จัดการ
        handle_event(body_str, x_line_signature)
    except Exception as e:
        # ถ้าพังที่ Signature ให้ส่ง 400
        print(f"Error handling LINE event: {e}")
        return {"status": "error", "message": str(e)}

    # ต้องส่ง 200 OK เสมอถ้า Signature ผ่าน
    return "OK"


@router.post("/create", response_model=CustomerCreate)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """
    Register a new customer (LINE User).
    """
    db_obj = Customer(**customer.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.get("/myrequest")
def get_my_repair_request(line_user_id: str, db: Session = Depends(get_db)):
    """
    Get the active repair request for the current user.
    """
    # ใช้ service แทนการดึงตรงๆ เพื่อลดการซ้ำซ้อนของโค้ด
    return get_repair_by_lineid(line_user_id, db)
