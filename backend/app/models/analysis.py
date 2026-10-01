from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.models.database import Base


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False, default="resume")
    resume_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    compatibility_score = Column(Float, default=0.0)
    ats_score = Column(Float, default=0.0)
    semantic_match = Column(Float, default=0.0)
    skill_match = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    json_output = Column(Text, nullable=True)
