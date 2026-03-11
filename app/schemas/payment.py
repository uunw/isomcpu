"""
Pydantic schemas for Payment.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PaymentBase(BaseModel):
    """
    Base schema for Payment data.
    """

    quotationId: int
    amount: float
    paymentDate: date
    paymentStatus: Optional[str] = "Pending"
    transactionId: Optional[str] = None


class PaymentCreate(PaymentBase):
    """
    Schema for creating a new Payment.
    """


class PaymentUpdate(BaseModel):
    """
    Schema for updating an existing Payment.
    """

    paymentStatus: Optional[str] = None
    transactionId: Optional[str] = None


class PaymentResponse(PaymentBase):
    """
    Schema for Payment data in responses.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)
