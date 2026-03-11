"""
Pydantic schemas for Repair Request.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RepairRequestBase(BaseModel):
    """
    Base schema for Repair Request data.
    """

    queueId: str
    lineUserId: str
    technicianID: Optional[int] = None
    deviceType: str
    problemType: str
    problemDetail: Optional[str] = None
    deliveryDate: Optional[date] = None
    pickupDate: Optional[date] = None
    address: Optional[str] = None
    status: Optional[str] = "คำขอส่งซ่อม"

    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None


class RepairRequestCreate(RepairRequestBase):
    """
    Schema for creating a new Repair Request.
    """


class RepairRequestUpdate(BaseModel):
    """
    Schema for updating an existing Repair Request.
    """

    technicianID: Optional[int] = None
    status: Optional[str] = None
    pickupDate: Optional[date] = None
    deliveryDate: Optional[date] = None


class RepairRequestResponse(RepairRequestBase):
    """
    Schema for Repair Request data in responses.
    """

    id: int
    createdAt: date
    updatedAt: date

    model_config = ConfigDict(from_attributes=True)
