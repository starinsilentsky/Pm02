from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    VISITOR = "visitor"
    RESEARCHER = "researcher"
    EDITOR = "editor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)

    oauth_provider = Column(String(20))
    oauth_id = Column(String(100))

    display_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(Text)

    role = Column(String(20), default=UserRole.VISITOR.value)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    contributions_count = Column(Integer, default=0)
    votes_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    articles = relationship("Article", back_populates="author")
    suggestions = relationship("MemeSuggestion", back_populates="user")


class MemeSuggestion(Base):
    __tablename__ = "meme_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    title = Column(String(255))
    description = Column(Text)
    image_url = Column(String(500))
    year = Column(Integer)
    source_url = Column(String(500))

    status = Column(String(20), default="pending")
    moderator_note = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="suggestions")
