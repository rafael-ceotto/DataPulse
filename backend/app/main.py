import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.auth_router import router as auth_router
from app.api.hospital_router import router
from app.core.database import AsyncSessionLocal
from app.services.hospital_service import ingest_hospitals
from app.services.infection_service import ingest_infections

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def run_scheduled_pipeline():
    print("=== SCHEDULED PIPELINE STARTING ===")
    async with AsyncSessionLocal() as session:
        try:
            hospitals = await ingest_hospitals(session)
            print(f"=== Scheduled pipeline: {hospitals} hospitals ingested ===")
        except Exception as e:
            print(f"=== Scheduled hospital pipeline failed: {e} ===")

    async with AsyncSessionLocal() as session:
        try:
            infections = await ingest_infections(session)
            print(f"=== Scheduled pipeline: {infections} infections ingested ===")
        except Exception as e:
            print(f"=== Scheduled infection pipeline failed: {e} ===")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.services.physician_analysis_service import get_national_specialty_counts
    asyncio.create_task(get_national_specialty_counts())

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_scheduled_pipeline,
        "interval",
        hours=6,
        
    )
    scheduler.start()
    print("=== Scheduler started — pipeline runs every 15 minutes for testing ===")

    yield

    # Shutdown
    scheduler.shutdown()
    print("=== Scheduler stopped ===")


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