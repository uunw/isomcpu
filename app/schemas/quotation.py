"""
Pydantic schemas for Quotation.
"""
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .quotation_item import QuotationItemResponse, QuotationItemCreate
from .repair_request import RepairRequestBase


class QuotationBase(BaseModel):
    """
    Base schema for Quotation data.
    """

    repairId: int
    totalPrice: float
    technicianNote: Optional[str] = None
    status: Optional[str] = "PendingConfirmation"


class QuotationCreate(BaseModel):
    """
    Schema for creating a new Quotation.
    """

    repairId: int
    totalPrice: float
    technicianNote: Optional[str] = None
    items: List[QuotationItemCreate]


class QuotationResponse(QuotationBase):
    """
    Schema for Quotation data in responses.
    """

    id: int
    createdAt: date
    items: List[QuotationItemResponse]

    model_config = ConfigDict(from_attributes=True)


class QuotationWithItemsResponse(BaseModel):
    """
    Extended schema for Quotation including nested items and repair info.
    """

    id: int
    repairId: int
    totalPrice: float
    technicianNote: Optional[str]
    status: str
    items: List[QuotationItemResponse]
    repair: RepairRequestBase

    model_config = ConfigDict(from_attributes=True)
