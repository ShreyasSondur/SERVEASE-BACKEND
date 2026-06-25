from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for guest searches
    emirate_id = Column(Integer, ForeignKey("emirates.id"), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    search_query = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    emirate = relationship("Emirate")
    city = relationship("City")
    category = relationship("Category")
