"""
Pydantic schemas for Quotation Item.
"""
from pydantic import BaseModel, ConfigDict


class QuotationItemBase(BaseModel):
    """
    Base schema for Quotation Item.
    """

    productName: str
    quantity: int = 1
    price: float


class QuotationItemCreate(QuotationItemBase):
    """
    Schema for creating a new Quotation Item.
    """


class QuotationItemResponse(QuotationItemBase):
    """
    Schema for Quotation Item in responses.
    """

    id: int
    quotationId: int

    model_config = ConfigDict(from_attributes=True)
