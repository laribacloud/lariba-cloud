import time
from collections import deque
from typing import Deque, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window limiter per API key.

    - Only limits requests that include X-API-Key.
    - Uses in-memory storage (dev/local).
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: Dict[str, Deque[float]] = {}

    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)

        now = time.time()
        q = self.hits.get(api_key)
        if q is None:
            q = deque()
            self.hits[api_key] = q

        # remove old timestamps
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= self.max_requests:
            retry_after = int(q[0] + self.window_seconds - now) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        q.append(now)
        return await call_next(request)
