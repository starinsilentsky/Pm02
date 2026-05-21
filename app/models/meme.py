from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid
from datetime import datetime


meme_tag_association = Table(
    "meme_tag_association",
    Base.metadata,
    Column("meme_id", UUID(as_uuid=True), ForeignKey("memes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

meme_similar_association = Table(
    "similar_memes",
    Base.metadata,
    Column("meme_id", UUID(as_uuid=True), ForeignKey("memes.id", ondelete="CASCADE"), primary_key=True),
    Column("similar_meme_id", UUID(as_uuid=True), ForeignKey("memes.id", ondelete="CASCADE"), primary_key=True),
    Column("similarity_score", Integer, default=0),
)


class Meme(Base):
    __tablename__ = "memes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    video_url = Column(String(500))
    format = Column(String(20), default="image")

    description = Column(Text)
    origin_story = Column(Text)
    cultural_context = Column(Text)

    year = Column(Integer, nullable=False, index=True)
    era_id = Column(UUID(as_uuid=True), ForeignKey("eras.id"), nullable=False)

    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    original_platform = Column(String(100))
    original_url = Column(String(500))

    status = Column(String(20), default="published")
    is_rare = Column(Boolean, default=False, index=True)
    is_nsfw = Column(Boolean, default=False)

    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)

    meta = Column(JSONB, default=dict)

    seo_title = Column(String(255))
    seo_description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    era = relationship("Era", back_populates="memes")
    source = relationship("Source", back_populates="memes")
    tags = relationship("Tag", secondary=meme_tag_association, back_populates="memes")
    similar_memes = relationship(
        "Meme",
        secondary=meme_similar_association,
        primaryjoin="Meme.id == meme_similar_association.c.meme_id",
        secondaryjoin="Meme.id == meme_similar_association.c.similar_meme_id",
        backref="related_to"
    )
