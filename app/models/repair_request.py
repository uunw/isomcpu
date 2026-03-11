"""
RepairRequest model for the application.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Date as SqlDate, DateTime
from sqlalchemy.orm import relationship
from ..database import Base


class RepairRequest(Base):
    """
    SQLAlchemy model for representing a repair request.
    """

    __tablename__ = "repairs_request"

    id = Column(Integer, primary_key=True, index=True)
    queueId = Column(String, unique=True, index=True)
    lineUserId = Column(String, index=True)
    technicianID = Column(Integer, ForeignKey("technicians.id"), nullable=True)

    # ข้อมูลเครื่องและอาการ
    deviceType = Column(String, nullable=False)
    problemType = Column(String, nullable=False)
    problemDetail = Column(String, nullable=True)

    # ข้อมูลวันที่
    deliveryDate = Column(SqlDate, nullable=True)  # วันที่ลูกค้ามาส่งเครื่อง
    pickupDate = Column(SqlDate, nullable=True)  # วันที่ลูกค้ามารับเครื่องคืน
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completedAt = Column(DateTime, nullable=True)

    # ข้อมูลติดต่อเพิ่มเติม (ถ้ามี)
    fullName = Column(String, nullable=True)
    phoneNumber = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # สถานะของงานซ่อม
    status = Column(String, default="PENDING_REPAIR")

    # ความสัมพันธ์
    technician = relationship("Technician")
    statusLogs = relationship("RepairStatusLog", back_populates="repairRequest", order_by="RepairStatusLog.changedAt")
    media = relationship("RepairMedia", back_populates="repairRequest", cascade="all, delete-orphan")
