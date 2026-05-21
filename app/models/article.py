from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid
from datetime import datetime


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    
    type = Column(String(50), default="article")
    
    content = Column(Text)
    excerpt = Column(Text)
    
    cover_image = Column(String(500))
    video_url = Column(String(500))
    
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    era_id = Column(UUID(as_uuid=True), ForeignKey("eras.id"))
    
    analyzed_meme_id = Column(UUID(as_uuid=True), ForeignKey("memes.id"))
    
    status = Column(String(20), default="draft")
    published_at = Column(DateTime)
    
    views_count = Column(Integer, default=0)
    read_time = Column(Integer, default=0)  # минуты
    
    meta = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = relationship("User", back_populates="articles")
    era = relationship("Era", back_populates="articles")
    analyzed_meme = relationship("Meme", foreign_keys=[analyzed_meme_id])
    tags = relationship("ArticleTag", back_populates="article")


class ArticleTag(Base):
    __tablename__ = "article_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"))
    tag = Column(String(50), nullable=False)
    
    article = relationship("Article", back_populates="tags")