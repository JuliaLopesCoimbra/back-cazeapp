from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.auth_db import Base


class DataRemovalRequest(Base):
    __tablename__ = "data_removal_requests"

    id = Column(Integer, primary_key=True, index=True)

    email_submitted = Column(String(255), nullable=False, index=True)
    cpf_submitted = Column(String(11), nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_name_snapshot = Column(String(150), nullable=True)

    status = Column(String(20), nullable=False, default="pending", index=True)
    # pending | completed | rejected

    match_found = Column(Boolean, default=False, nullable=False)

    request_ip = Column(String(45), nullable=True)
    request_user_agent = Column(String(1000), nullable=True)

    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    processed_by = relationship("User", foreign_keys=[processed_by_id])
