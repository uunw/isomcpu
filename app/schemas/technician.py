"""
Pydantic schemas for Technician.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class TechnicianBase(BaseModel):
    """
    Base schema for Technician data.
    """

    email: EmailStr
    displayName: str
    firstName: str
    lastName: str
    phoneNumber: str


class TechnicianCreate(TechnicianBase):
    """
    Schema for creating a new Technician.
    """

    password: str


class TechnicianUpdate(BaseModel):
    """
    Schema for updating an existing Technician.
    """

    email: Optional[EmailStr] = None
    displayName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None
    password: Optional[str] = None


class TechnicianResponse(TechnicianBase):
    """
    Schema for Technician data in responses.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Schema for Authentication Token.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema for Token Payload data.
    """

    email: Optional[str] = None
