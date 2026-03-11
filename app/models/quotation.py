"""
Quotation model for the application.
"""
from datetime import date
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date as SqlDate
from sqlalchemy.orm import relationship
from ..database import Base


class Quotation(Base):
    """
    SQLAlchemy model for representing a quotation.
    """

    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    repairId = Column(Integer, ForeignKey("repairs_request.id"))
    totalPrice = Column(Float, nullable=False)
    technicianNote = Column(String, nullable=True)
    createdAt = Column(SqlDate, default=date.today)
    status = Column(String, default="PendingConfirmation")

    # ความสัมพันธ์
    repair = relationship("RepairRequest")
    items = relationship("QuotationItem", back_populates="quotation")
