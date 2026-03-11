from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class RepairMedia(Base):
    """
    Model for storing information about uploaded images and videos for a repair request.
    """
    __tablename__ = "repair_media"

    id = Column(Integer, primary_key=True, index=True)
    repairId = Column(Integer, ForeignKey("repairs_request.id"), index=True)
    fileUrl = Column(String, nullable=False) # Path to file
    fileType = Column(String, nullable=False) # 'image' or 'video'
    section = Column(String, nullable=False) # 'BEFORE', 'INITIAL', 'DURING', 'AFTER'
    uploadedAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    repairRequest = relationship("RepairRequest", back_populates="media")

# Update RepairRequest model to include the relationship
