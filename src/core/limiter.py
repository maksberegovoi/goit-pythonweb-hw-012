from fastapi import Request

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )