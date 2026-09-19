from __future__ import annotations

from sqlalchemy import Column, Float, Integer, String, Text

from app.models.database import Base


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    resume_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    compatibility_score = Column(Float, default=0.0)
    semantic_match = Column(Float, default=0.0)
    skill_match = Column(Float, default=0.0)
    json_output = Column(Text, nullable=True)
