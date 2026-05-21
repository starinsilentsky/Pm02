from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid
from datetime import datetime


class Era(Base):
    __tablename__ = "eras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), unique=True, nullable=False)

    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True)

    description = Column(Text)
    cultural_context = Column(Text)
    key_events = Column(JSONB, default=list)

    cover_image = Column(String(500))
    timeline_data = Column(JSONB, default=dict)

    color = Column(String(7), default="#FF6B6B")

    created_at = Column(DateTime, default=datetime.utcnow)

    memes = relationship("Meme", back_populates="era")
    articles = relationship("Article", back_populates="era")
    sources = relationship("Source", back_populates="era")


class EraMapPoint(Base):
    __tablename__ = "era_map_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    era_id = Column(UUID(as_uuid=True), ForeignKey("eras.id", ondelete="CASCADE"))

    lat = Column(Numeric(9, 6), nullable=False)
    lng = Column(Numeric(9, 6), nullable=False)

    title = Column(String(255))
    description = Column(Text)
    type = Column(String(50), default="meme_origin")

    era = relationship("Era", backref="map_points")
