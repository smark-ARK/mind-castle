from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.types import ASGIApp

from .database import engine
from app.models import Base
from app.routers import auth, notes
from app.utils import TokenBucket


app = FastAPI()

# models.Base.metadata.create_all(bind=engine)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, bucket: TokenBucket) -> None:
        super().__init__(app)
        self.bucket = bucket

    async def dispatch(self, request: Request, call_next):
        if self.bucket.take_token():
            return await call_next(request)
        error_response = JSONResponse(
            content={"detail": "Rate Limit Exceeded"},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
        raise HTTPException(
            detail="Rate Limit Exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


bucket = TokenBucket(capacity=15, refill_rate=2)

# app.add_middleware(RateLimitMiddleware, bucket=bucket)


app.include_router(auth.router)
app.include_router(notes.router)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://*",
    "http://127.0.0.1:8000",
    "https://simple-social-smark.netlify.app",
    "http://127.0.0.1:3000",
    "localhost:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Hello World!"}
