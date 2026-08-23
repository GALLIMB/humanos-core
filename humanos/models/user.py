from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from ..db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    language = Column(String, default="ar")
    
    # ===== حقول الملف الشخصي الجديدة (الخيار 1 و 4) =====
    age = Column(Integer, nullable=True)
    job_title = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=True)
    skills = Column(String, nullable=True)  # نخزنها كنص مفصول بفواصل
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())