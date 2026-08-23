from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from ..db.session import Base

class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    gaps = Column(Text, nullable=True)
    solutions = Column(Text, nullable=True)
    action_plan = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())