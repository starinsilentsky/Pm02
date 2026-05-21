from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.database import get_db
from app.models.meme import Meme
from app.models.article import Article
from app.models.tag import Tag
from app.models.era import Era

router = APIRouter(prefix="/search", tags=["Поиск"])

@router.get("/", response_model=dict)
async def global_search(
    q: str = Query(..., min_length=2, max_length=100),
    type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    
    search = f"%{q}%"
    results = {"query": q, "sections": {}}

    if type in (None, "all", "memes"):
        meme_query = select(Meme).where(
            and_(
                Meme.status == "published",
                or_(
                    Meme.title.ilike(search),
                    Meme.description.ilike(search),
                    Meme.origin_story.ilike(search),
                    Meme.cultural_context.ilike(search)
                )
            )
        ).options(
            selectinload(Meme.era),
            selectinload(Meme.tags)
        ).limit(limit)

        meme_result = await db.execute(meme_query)
        memes = meme_result.scalars().all()

        results["sections"]["memes"] = {
            "count": len(memes),
            "items": [
                {
                    "id": str(m.id),
                    "title": m.title,
                    "slug": m.slug,
                    "image_url": m.thumbnail_url or m.image_url,
                    "year": m.year,
                    "era": m.era.name if m.era else None,
                    "type": "meme"
                }
                for m in memes
            ]
        }

    if type in (None, "all", "articles"):
        article_query = select(Article).where(
            and_(
                Article.status == "published",
                or_(
                    Article.title.ilike(search),
                    Article.excerpt.ilike(search),
                    Article.content.ilike(search)
                )
            )
        ).options(
            selectinload(Article.era)
        ).limit(limit)

        article_result = await db.execute(article_query)
        articles = article_result.scalars().all()

        results["sections"]["articles"] = {
            "count": len(articles),
            "items": [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "slug": a.slug,
                    "excerpt": (a.excerpt[:200] + "...") if a.excerpt and len(a.excerpt) > 200 else a.excerpt,
                    "type": a.type,
                    "cover_image": a.cover_image,
                    "era": a.era.name if a.era else None
                }
                for a in articles
            ]
        }

    if type in (None, "all", "tags"):
        tag_query = select(Tag).where(
            or_(
                Tag.name.ilike(search),
                Tag.description.ilike(search)
            )
        ).limit(limit)

        tag_result = await db.execute(tag_query)
        tags = tag_result.scalars().all()

        results["sections"]["tags"] = {
            "count": len(tags),
            "items": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "category": t.category,
                    "usage_count": t.usage_count
                }
                for t in tags
            ]
        }

    if type in (None, "all", "eras"):
        era_query = select(Era).where(
            or_(
                Era.name.ilike(search),
                Era.description.ilike(search),
                Era.cultural_context.ilike(search)
            )
        ).limit(limit)

        era_result = await db.execute(era_query)
        eras = era_result.scalars().all()

        results["sections"]["eras"] = {
            "count": len(eras),
            "items": [
                {
                    "id": str(e.id),
                    "name": e.name,
                    "slug": e.slug,
                    "period": f"{e.start_year}-{e.end_year or 'н.в.'}",
                    "color": e.color
                }
                for e in eras
            ]
        }

    results["total"] = sum(s["count"] for s in results["sections"].values())

    return results

@router.get("/autocomplete", response_model=List[dict])
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    
    search = f"%{q}%"
    suggestions = []

    meme_query = select(Meme).where(
        and_(Meme.status == "published", Meme.title.ilike(search))
    ).limit(limit // 2)
    meme_result = await db.execute(meme_query)
    for m in meme_result.scalars().all():
        suggestions.append({
            "text": m.title,
            "type": "meme",
            "slug": m.slug,
        })

    tag_query = select(Tag).where(Tag.name.ilike(search)).limit(limit // 4)
    tag_result = await db.execute(tag_query)
    for t in tag_result.scalars().all():
        suggestions.append({
            "text": f"#{t.name}",
            "type": "tag",
            "slug": t.slug,
        })

    era_query = select(Era).where(Era.name.ilike(search)).limit(limit // 4)
    era_result = await db.execute(era_query)
    for e in era_result.scalars().all():
        suggestions.append({
            "text": e.name,
            "type": "era",
            "slug": e.slug,
        })

    return suggestions[:limit]
