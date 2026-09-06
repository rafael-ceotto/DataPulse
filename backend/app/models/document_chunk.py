from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    page = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, server_default=func.now())