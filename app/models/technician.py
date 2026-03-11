"""
Technician model for the application.
"""
from sqlalchemy import Column, Integer, String
from ..database import Base


class Technician(Base):
    """
    SQLAlchemy model for representing a technician.
    """

    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # เก็บแบบ Hashed Password
    displayName = Column(String)
    firstName = Column(String)
    lastName = Column(String)
    phoneNumber = Column(String)
