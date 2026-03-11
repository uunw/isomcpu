"""
Payment model for the application.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from ..database import Base


class Payment(Base):
    """
    SQLAlchemy model for representing a payment.
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    quotationId = Column(Integer, ForeignKey("quotations.id"))
    amount = Column(Float, nullable=False)
    paymentDate = Column(Date, nullable=False)
    paymentStatus = Column(String, default="Pending")  # เช่น Pending, Success, Failed
    transactionId = Column(String, nullable=True)

    # ความสัมพันธ์
    quotation = relationship("Quotation")
