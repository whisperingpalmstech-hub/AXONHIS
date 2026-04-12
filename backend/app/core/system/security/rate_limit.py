import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    HIPAA-grade rate limiting to prevent brute force and scraping of patient data.
    """
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.visit_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        if client_ip not in self.visit_counts:
            self.visit_counts[client_ip] = []
        
        # Cleanup old timestamps
        self.visit_counts[client_ip] = [t for t in self.visit_counts[client_ip] if now - t < 60]
        
        if len(self.visit_counts[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. HIPAA security policy enforced rate limit."
            )
        
        self.visit_counts[client_ip].append(now)
        return await call_next(request)
