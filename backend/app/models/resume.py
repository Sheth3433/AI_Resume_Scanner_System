from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text

from app.models.database import Base


class ResumeRecord(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=False)
    stored_path = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=True)
