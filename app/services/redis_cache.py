import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_cache(key: str):
    try:
        return await redis_client.get(key)
    except Exception:
        return None


async def set_cache(key: str, value: str, expire: int = 300):
    try:
        await redis_client.set(key, value, ex=expire)
    except Exception:
        pass


async def delete_cache(key: str):
    try:
        await redis_client.delete(key)
    except Exception:
        pass
