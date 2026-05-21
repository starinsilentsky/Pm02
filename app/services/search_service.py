from elasticsearch import AsyncElasticsearch
from app.config import get_settings

settings = get_settings()

es = AsyncElasticsearch([settings.ELASTICSEARCH_URL]) if settings.ELASTICSEARCH_URL else None

async def index_meme(meme):
    
    if not es:
        return
    
    await es.index(
        index="memes",
        id=str(meme.id),
        document={
            "title": meme.title,
            "description": meme.description,
            "origin_story": meme.origin_story,
            "cultural_context": meme.cultural_context,
            "year": meme.year,
            "tags": [t.name for t in meme.tags],
            "era": meme.era.name if meme.era else None,
            "status": meme.status
        }
    )

async def search_memes(query: str, filters: dict = None, size: int = 24):
    
    if not es:
        return []
    
    must = [{"multi_match": {
        "query": query,
        "fields": ["title^3", "description^2", "origin_story", "cultural_context", "tags^2"]
    }}]
    
    if filters:
        for key, value in filters.items():
            must.append({"term": {key: value}})
    
    response = await es.search(
        index="memes",
        body={
            "query": {"bool": {"must": must}},
            "size": size,
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {"fragment_size": 150}
                }
            }
        }
    )
    
    return response["hits"]["hits"]
