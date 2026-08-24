import redis.asyncio as aioredis
import json
from typing import Any

redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

async def get_cache(key: str) -> Any | None:
    value = await redis_client.get(key)
    if value:
        return json.loads(value)
    return None

async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    result = await redis_client.set(key, json.dumps(value), ex=ttl)
   
    
async def invalidate_cache(pattern: str) -> None:
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)