from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.database import get_db
from app.models.meme import Meme
from app.models.tag import Tag
from app.models.era import Era
from app.schemas.meme import MemeCard, MemeDetail, MemeFilter, MemeCreate
from app.utils.auth import get_current_user_optional, require_editor
from uuid import UUID
import re
import uuid as uuid_mod

router = APIRouter(prefix="/gallery", tags=["Галерея"])

SORT_FIELDS = {
    "created_at": Meme.created_at,
    "year": Meme.year,
    "views_count": Meme.views_count,
    "likes_count": Meme.likes_count,
}

@router.get("/memes", response_model=dict)
async def list_memes(
    filter_params: MemeFilter = Depends(),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Meme).where(Meme.status == (filter_params.status or "published"))

    if filter_params.era:
        query = query.join(Era).where(Era.slug == filter_params.era)

    if filter_params.tag:
        query = query.join(Meme.tags).where(Tag.slug == filter_params.tag)

    if filter_params.year_from:
        query = query.where(Meme.year >= filter_params.year_from)
    if filter_params.year_to:
        query = query.where(Meme.year <= filter_params.year_to)

    if filter_params.format:
        query = query.where(Meme.format == filter_params.format)

    if filter_params.search:
        search = f"%{filter_params.search}%"
        query = query.where(
            or_(
                Meme.title.ilike(search),
                Meme.description.ilike(search),
                Meme.origin_story.ilike(search)
            )
        )

    sort_field = SORT_FIELDS.get(filter_params.sort_by, Meme.created_at)
    if filter_params.order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    offset = (filter_params.page - 1) * filter_params.page_size
    query = query.offset(offset).limit(filter_params.page_size)

    query = query.options(
        selectinload(Meme.era),
        selectinload(Meme.tags),
        selectinload(Meme.source)
    )

    result = await db.execute(query)
    memes = result.scalars().all()

    return {
        "items": [MemeCard.model_validate(m) for m in memes],
        "total": total,
        "page": filter_params.page,
        "page_size": filter_params.page_size,
        "pages": (total + filter_params.page_size - 1) // filter_params.page_size
    }

@router.get("/memes/{slug}", response_model=MemeDetail)
async def get_meme(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Meme).where(Meme.slug == slug).options(
        selectinload(Meme.era),
        selectinload(Meme.tags),
        selectinload(Meme.source),
        selectinload(Meme.similar_memes).selectinload(Meme.era),
        selectinload(Meme.similar_memes).selectinload(Meme.tags)
    )

    result = await db.execute(query)
    meme = result.scalar_one_or_none()

    if not meme:
        raise HTTPException(status_code=404, detail="Мем не найден")

    await db.execute(
        update(Meme).where(Meme.id == meme.id).values(views_count=Meme.views_count + 1)
    )
    await db.commit()
    await db.refresh(meme)

    return MemeDetail.model_validate(meme)

@router.get("/memes/{meme_id}/similar", response_model=List[MemeCard])
async def get_similar_memes(
    meme_id: UUID,
    limit: int = Query(4, ge=1, le=12),
    db: AsyncSession = Depends(get_db)
):
    
    meme_query = select(Meme).where(Meme.id == meme_id).options(
        selectinload(Meme.tags)
    )
    result = await db.execute(meme_query)
    meme = result.scalar_one_or_none()

    if not meme:
        raise HTTPException(status_code=404, detail="Мем не найден")

    tag_ids = [t.id for t in meme.tags]

    similar_query = select(Meme).where(
        and_(
            Meme.id != meme_id,
            Meme.status == "published"
        )
    ).options(
        selectinload(Meme.era),
        selectinload(Meme.tags)
    )

    if tag_ids:
        similar_query = similar_query.join(Meme.tags).where(Tag.id.in_(tag_ids))

    similar_query = similar_query.order_by(Meme.likes_count.desc()).limit(limit)

    result = await db.execute(similar_query)
    similar = result.scalars().all()

    return [MemeCard.model_validate(m) for m in similar]

@router.get("/filter/eras", response_model=List[dict])
async def get_filter_eras(db: AsyncSession = Depends(get_db)):
    
    query = select(Era).order_by(Era.start_year)
    result = await db.execute(query)
    eras = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "name": e.name,
            "slug": e.slug,
            "start_year": e.start_year,
            "end_year": e.end_year,
            "color": e.color,
        }
        for e in eras
    ]

@router.get("/filter/tags", response_model=List[dict])
async def get_filter_tags(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Tag).order_by(Tag.usage_count.desc())
    if category:
        query = query.where(Tag.category == category)

    result = await db.execute(query)
    tags = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "category": t.category,
            "color": t.color,
            "count": t.usage_count
        }
        for t in tags
    ]

@router.post("/memes", response_model=MemeCard, status_code=201)
async def create_meme(
    meme_data: MemeCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor)
):
    
    base_slug = re.sub(r'[^\w\s-]', '', meme_data.title.lower())
    base_slug = re.sub(r'[-\s]+', '-', base_slug)
    slug = base_slug[:50]

    existing = await db.execute(select(Meme).where(Meme.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{base_slug[:45]}-{str(uuid_mod.uuid4())[:8]}"

    meme = Meme(
        title=meme_data.title,
        slug=slug,
        description=meme_data.description,
        year=meme_data.year,
        era_id=meme_data.era_id,
        source_id=meme_data.source_id,
        original_platform=meme_data.original_platform,
        is_nsfw=meme_data.is_nsfw,
        status="draft"
    )

    if meme_data.tags:
        tag_query = select(Tag).where(Tag.slug.in_(meme_data.tags))
        tag_result = await db.execute(tag_query)
        tags = tag_result.scalars().all()
        meme.tags = tags

    db.add(meme)
    await db.commit()
    await db.refresh(meme)

    return MemeCard.model_validate(meme)
