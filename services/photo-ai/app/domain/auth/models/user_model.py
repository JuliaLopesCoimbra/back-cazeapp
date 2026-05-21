from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.auth_db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
    email = Column(String(180), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    profile_photo = Column(String(500), nullable=True)
    role = Column(String(20), default="user")
    is_email_verified = Column(Boolean, default=False)
    status = Column(String(20), default="active")

    birth_date = Column(DateTime(timezone=True), nullable=True)
    age_verified = Column(Boolean, default=False)

    cpf = Column(String(11), nullable=True, unique=True)
    gender = Column(String(20), nullable=True)

    lgpd_accepted = Column(Boolean, default=False)
    age_terms_accepted = Column(Boolean, default=False)
    marketing_email_accepted = Column(Boolean, default=False)

    lgpd_accepted_at = Column(DateTime(timezone=True), nullable=True)
    lgpd_accepted_ip = Column(String(45), nullable=True)
    lgpd_accepted_user_agent = Column(String(1000), nullable=True)

    age_terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    age_terms_accepted_ip = Column(String(45), nullable=True)
    age_terms_accepted_user_agent = Column(String(1000), nullable=True)

    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_by = relationship("User", remote_side=[id], foreign_keys=[invited_by_id])

    deactivated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_by = relationship("User", remote_side=[id], foreign_keys=[deactivated_by_id])

    reactivated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reactivated_at = Column(DateTime(timezone=True), nullable=True)
    reactivated_by = relationship("User", remote_side=[id], foreign_keys=[reactivated_by_id])

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    last_login = Column(DateTime(timezone=True), nullable=True)
