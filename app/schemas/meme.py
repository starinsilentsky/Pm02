from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TagBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class EraBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    start_year: int
    end_year: Optional[int] = None
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class SourceBrief(BaseModel):
    id: UUID
    name: str
    slug: str
    platform: Optional[str] = None

    model_config = {"from_attributes": True}


class MemeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    year: int = Field(..., ge=1990, le=2030)
    era_id: UUID
    tags: List[str] = []
    source_id: Optional[UUID] = None
    original_platform: Optional[str] = None
    is_nsfw: bool = False


class MemeCreate(MemeBase):
    pass


class MemeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    era_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_rare: Optional[bool] = None


class MemeCard(BaseModel):
    id: UUID
    slug: str
    title: str
    description: Optional[str] = None
    year: int
    image_url: str
    thumbnail_url: Optional[str] = None
    format: str
    status: str
    is_rare: bool
    is_nsfw: bool
    views_count: int
    likes_count: int
    era: EraBrief
    tags: List[TagBrief]
    source_id: Optional[UUID] = None
    original_platform: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemeDetail(MemeCard):
    origin_story: Optional[str] = None
    cultural_context: Optional[str] = None
    original_url: Optional[str] = None
    source: Optional[SourceBrief] = None
    meta: Optional[dict] = None
    similar_memes: List[MemeCard] = []
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemeFilter(BaseModel):
    era: Optional[str] = None
    tag: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    format: Optional[str] = None
    status: Optional[str] = "published"
    search: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    order: Optional[str] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)
