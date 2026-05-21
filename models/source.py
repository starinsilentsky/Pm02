from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid
from datetime import datetime


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    type = Column(String(50), default="platform")
    platform = Column(String(50))
    
    description = Column(Text)
    url = Column(String(500))
    
    meta = Column(JSONB, default=dict)
    
    era_id = Column(UUID(as_uuid=True), ForeignKey("eras.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memes = relationship("Meme", back_populates="source")
    era = relationship("Era", back_populates="sources")