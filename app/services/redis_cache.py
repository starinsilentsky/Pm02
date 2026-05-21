import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5
)

async def cache_get(key: str):
    
    try:
        return await redis_client.get(key)
    except Exception:
        return None

async def cache_set(key: str, value: str, expire: int = 3600):
    
    try:
        await redis_client.setex(key, expire, value)
    except Exception:
        pass

async def cache_delete(key: str):
    
    try:
        await redis_client.delete(key)
    except Exception:
        pass

async def increment_counter(key: str, expire: int = 86400):
    
    try:
        await redis_client.incr(key)
        await redis_client.expire(key, expire)
    except Exception:
        pass
