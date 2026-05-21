from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EraMapPointSchema(BaseModel):
    id: UUID
    lat: float
    lng: float
    title: str
    description: Optional[str] = None
    type: str

    model_config = {"from_attributes": True}


class EraBase(BaseModel):
    name: str
    slug: str
    start_year: int
    end_year: Optional[int] = None
    description: Optional[str] = None
    color: Optional[str] = "#FF6B6B"


class EraCreate(EraBase):
    pass


class EraDetail(EraBase):
    id: UUID
    cultural_context: Optional[str] = None
    key_events: Optional[List[dict]] = []
    cover_image: Optional[str] = None
    timeline_data: Optional[dict] = None
    map_points: List[EraMapPointSchema] = []
    memes_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEntry(BaseModel):
    year: int
    title: str
    description: Optional[str] = None
    memes_count: int
    key_memes: List[dict] = []
