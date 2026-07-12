from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Emirate(Base):
    __tablename__ = "emirates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)

    cities = relationship("City", back_populates="emirate")

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    emirate_id = Column(Integer, ForeignKey("emirates.id"), nullable=False)
    name = Column(String, index=True, nullable=False)

    emirate = relationship("Emirate", back_populates="cities")
    services = relationship("Service", back_populates="city")
    deals = relationship("Deal", back_populates="city", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    services = relationship("Service", back_populates="category")
    deals = relationship("Deal", back_populates="category", cascade="all, delete-orphan")
