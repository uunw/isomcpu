"""
Service layer for handling quotations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.quotation import Quotation
from ..models.quotation_item import QuotationItem
from ..schemas.quotation import QuotationCreate

def create_repair_quotation(db: Session, obj_in: QuotationCreate) -> Quotation:
    """
    Business logic for creating a quotation with items.
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
        return new_quotation
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
