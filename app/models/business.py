from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partner_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    images = Column(JSON, default=list)
    emergency_service = Column(String, nullable=True, default="Available 24/7")
    provider_type = Column(String, nullable=True, default="Licensed Company")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    partner = relationship("PartnerProfile", back_populates="services")
    category = relationship("Category", back_populates="services")
    city = relationship("City", back_populates="services")

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partner_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    images = Column(JSON, default=list)
    discount_desc = Column(String, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    partner = relationship("PartnerProfile", back_populates="deals")
    category = relationship("Category", back_populates="deals")
    city = relationship("City", back_populates="deals")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="activity_logs")
