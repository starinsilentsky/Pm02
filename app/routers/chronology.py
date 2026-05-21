from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.era import Era
from app.models.meme import Meme
from app.schemas.era import EraDetail, TimelineEntry, EraCreate
from app.utils.auth import require_editor

router = APIRouter(prefix="/chronology", tags=["Хронология"])

@router.get("/eras", response_model=List[EraDetail])
async def list_eras(db: AsyncSession = Depends(get_db)):
    
    query = select(Era).options(
        selectinload(Era.map_points),
        selectinload(Era.memes)
    ).order_by(Era.start_year)

    result = await db.execute(query)
    eras = result.scalars().all()

    response = []
    for era in eras:
        era_data = EraDetail.model_validate(era)
        era_data.memes_count = len(era.memes)
        response.append(era_data)

    return response

@router.get("/eras/{slug}", response_model=EraDetail)
async def get_era(
    slug: str,
    include_memes: bool = True,
    db: AsyncSession = Depends(get_db)
):
    
    opts = [selectinload(Era.map_points), selectinload(Era.sources)]
    if include_memes:
        opts.append(selectinload(Era.memes))

    query = select(Era).where(Era.slug == slug).options(*opts)
    result = await db.execute(query)
    era = result.scalar_one_or_none()

    if not era:
        raise HTTPException(status_code=404, detail="Эпоха не найдена")

    era_data = EraDetail.model_validate(era)
    era_data.memes_count = len(era.memes) if era.memes else 0

    return era_data

@router.get("/timeline", response_model=List[TimelineEntry])
async def get_timeline(
    era_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    
    count_query = select(
        Meme.year,
        func.count(Meme.id).label("memes_count")
    ).where(Meme.status == "published")

    if era_slug:
        count_query = count_query.join(Era).where(Era.slug == era_slug)

    count_query = count_query.group_by(Meme.year).order_by(Meme.year)
    years_data = (await db.execute(count_query)).all()

    if not years_data:
        return []

    years = [row.year for row in years_data]

    subq = (
        select(
            Meme.id,
            Meme.year,
            func.row_number().over(
                partition_by=Meme.year,
                order_by=Meme.likes_count.desc()
            ).label("rn")
        )
        .where(and_(Meme.year.in_(years), Meme.status == "published"))
        .subquery()
    )

    top_query = (
        select(Meme)
        .join(subq, Meme.id == subq.c.id)
        .where(subq.c.rn <= 3)
        .options(selectinload(Meme.tags))
    )
    top_result = await db.execute(top_query)
    all_top_memes = top_result.scalars().all()

    memes_by_year: dict[int, list] = {y: [] for y in years}
    for m in all_top_memes:
        memes_by_year[m.year].append(m)

    timeline = []
    for row in years_data:
        key_memes = memes_by_year.get(row.year, [])
        timeline.append(TimelineEntry(
            year=row.year,
            title=str(row.year),
            memes_count=row.memes_count,
            key_memes=[
                {
                    "id": str(m.id),
                    "title": m.title,
                    "slug": m.slug,
                    "image_url": m.image_url,
                    "thumbnail_url": m.thumbnail_url
                }
                for m in key_memes
            ]
        ))

    return timeline

@router.get("/map/{era_slug}", response_model=List[dict])
async def get_era_map(
    era_slug: str,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Era).where(Era.slug == era_slug).options(
        selectinload(Era.map_points)
    )
    result = await db.execute(query)
    era = result.scalar_one_or_none()

    if not era:
        raise HTTPException(status_code=404, detail="Эпоха не найдена")

    return [
        {
            "id": str(p.id),
            "lat": float(p.lat),
            "lng": float(p.lng),
            "title": p.title,
            "description": p.description,
            "type": p.type
        }
        for p in era.map_points
    ]

@router.get("/context/{era_slug}", response_model=dict)
async def get_era_context(
    era_slug: str,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Era).where(Era.slug == era_slug).options(
        selectinload(Era.sources)
    )
    result = await db.execute(query)
    era = result.scalar_one_or_none()

    if not era:
        raise HTTPException(status_code=404, detail="Эпоха не найдена")

    return {
        "era": {
            "id": str(era.id),
            "name": era.name,
            "period": f"{era.start_year}-{era.end_year or 'н.в.'}",
            "description": era.description,
            "cultural_context": era.cultural_context,
            "color": era.color
        },
        "key_events": era.key_events or [],
        "sources": [
            {
                "id": str(s.id),
                "name": s.name,
                "platform": s.platform,
                "url": s.url
            }
            for s in (era.sources or [])
        ]
    }

@router.post("/eras", response_model=EraDetail, status_code=201)
async def create_era(
    era_data: EraCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_editor)
):
    
    era = Era(**era_data.model_dump())
    db.add(era)
    await db.commit()
    await db.refresh(era)
    return EraDetail.model_validate(era)
