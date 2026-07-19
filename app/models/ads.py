from sqlalchemy import Column, Integer, String, Boolean
from app.db.base_class import Base

class AdConfig(Base):
    __tablename__ = "ad_configs"

    id = Column(Integer, primary_key=True, index=True)
    position = Column(String, unique=True, index=True) # "add1", "add2"
    image_url = Column(String, nullable=True)
    redirect_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
