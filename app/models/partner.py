from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
from app.db.base_class import Base

class PartnerStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    PAYMENT_EXPIRED = "PAYMENT_EXPIRED"

class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String, nullable=False, default="")
    last_name = Column(String, nullable=False, default="")
    phone = Column(String, nullable=False, default="")
    emirate = Column(String, nullable=False, default="")
    city = Column(String, nullable=False, default="")
    emirate_id_number = Column(String, nullable=False, default="")
    business_name = Column(String, index=True, nullable=True)
    emirates_id_url = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    status = Column(Enum(PartnerStatus), default=PartnerStatus.PENDING, nullable=False)
    services_limit = Column(Integer, default=6)
    deals_limit = Column(Integer, default=2)
    suspended_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="partner_profile")
    services = relationship("Service", back_populates="partner")
    deals = relationship("Deal", back_populates="partner")

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""
