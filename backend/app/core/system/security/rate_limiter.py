import time
from fastapi import Request, HTTPException
import redis.asyncio as redis
from app.config import settings

redis_client = None

async def init_redis():
    global redis_client
    if not redis_client:
        redis_client = redis.from_url(settings.redis_dsn, encoding="utf-8", decode_responses=True)

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window

    async def __call__(self, request: Request):
        await init_redis()
        # Fallback if no redis
        if not redis_client:
            return

        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        
        current = await redis_client.get(key)
        if current and int(current) >= self.requests:
            raise HTTPException(status_code=429, detail="Too Many Requests")
            
        pipe = redis_client.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, self.window)
        await pipe.execute()

# Use as: Depends(RateLimiter(requests=100, window=60))
