from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

class RepairStatusLog(Base):
    """
    Model for tracking the history of status changes for a repair request.
    """
    __tablename__ = "repair_status_logs"

    id = Column(Integer, primary_key=True, index=True)
    repairRequestId = Column(Integer, ForeignKey("repairs_request.id"), index=True)
    status = Column(String, nullable=False)
    changedAt = Column(DateTime, default=datetime.utcnow)
    changedBy = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    note = Column(String, nullable=True)

    # Relationships
    repairRequest = relationship("RepairRequest", back_populates="statusLogs")
    technician = relationship("Technician")
