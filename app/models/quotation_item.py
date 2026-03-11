"""
QuotationItem model for the application.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from ..database import Base


class QuotationItem(Base):
    """
    SQLAlchemy model for representing an item in a quotation.
    """

    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True)
    quotationId = Column(Integer, ForeignKey("quotations.id"))
    productName = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    # ความสัมพันธ์
    quotation = relationship("Quotation", back_populates="items")
