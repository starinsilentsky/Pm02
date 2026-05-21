from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(50), unique=True, nullable=False)
    
    category = Column(String(50), default="general")  
    
    description = Column(Text)
    color = Column(String(7), default="#4ECDC4")
    
    usage_count = Column(Integer, default=0)
    
    is_nsfw = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memes = relationship("Meme", secondary="meme_tag_association", back_populates="tags")