"""
Customer model for the application.
"""
from sqlalchemy import Column, Integer, String
from ..database import Base


class Customer(Base):
    """
    SQLAlchemy model for representing a customer.
    """

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    lineUserId = Column(String, unique=True, index=True)
    displayName = Column(String, nullable=True)
    firstName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)
    phoneNumber = Column(String, nullable=True)
