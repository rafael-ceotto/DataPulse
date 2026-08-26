import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.auth_router import router as auth_router
from app.api.hospital_router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — warm national specialty cache in background
    from app.services.physician_analysis_service import get_national_specialty_counts
    asyncio.create_task(get_national_specialty_counts())
    yield
    # Shutdown


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "DataPulse API"}


@app.get("/health")
def health():
    return {"status": "ok"}