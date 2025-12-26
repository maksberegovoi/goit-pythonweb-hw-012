from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from src.api import users, auth
from src.api.contacts import router as contacts_router
from fastapi.middleware.cors import CORSMiddleware

from src.core.limiter import rate_limit_handler

app = FastAPI()


origins = [
    "<http://localhost:3000>"
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.include_router(contacts_router)
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")