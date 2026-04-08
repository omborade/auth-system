import redis.asyncio as aioredis
from app.config import settings

# ─── Singleton Redis Client ───────────────────────────────────────────────────
redis_client: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


# ─── Token Helpers ────────────────────────────────────────────────────────────

async def cache_token(user_id: int, token: str, ttl_seconds: int):
    """Store JWT in Redis with expiry."""
    r = await get_redis()
    await r.set(f"token:user:{user_id}", token, ex=ttl_seconds)


async def get_cached_token(user_id: int) -> str | None:
    r = await get_redis()
    return await r.get(f"token:user:{user_id}")


async def blacklist_token(token: str, ttl_seconds: int):
    """Add token to blacklist (logout). TTL = remaining validity."""
    r = await get_redis()
    await r.set(f"blacklist:{token}", "1", ex=ttl_seconds)


async def is_token_blacklisted(token: str) -> bool:
    r = await get_redis()
    result = await r.get(f"blacklist:{token}")
    return result is not None


async def delete_user_token(user_id: int):
    """Remove cached token on logout."""
    r = await get_redis()
    await r.delete(f"token:user:{user_id}")
