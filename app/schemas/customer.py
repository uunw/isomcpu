"""
Pydantic schemas for Customer.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    """
    Base schema for Customer data.
    """

    lineUserId: str
    displayName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None


class CustomerCreate(CustomerBase):
    """
    Schema for creating a new Customer.
    """


class CustomerUpdate(BaseModel):
    """
    Schema for updating an existing Customer.
    """

    displayName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None


class CustomerResponse(CustomerBase):
    """
    Schema for Customer data in responses.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)
