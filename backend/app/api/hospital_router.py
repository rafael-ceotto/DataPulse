from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.hospital_service import ingest_hospitals
from app.repositories.hospital_repository import get_hospitals, get_hospitals_by_id, save_hospitals, get_rating_distribution
from app.ai.hospital_ai_service import ask_hospital_ai
from app.services.infection_service import ingest_infections
from app.repositories.infection_repository import get_infections, get_infections_by_facility


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

class AIQueryRequest(BaseModel):
    question: str

@router.post("/api/v1/pipeline/run")
async def run_pipeline(session: AsyncSession = Depends(get_session)):
    counter = await ingest_hospitals(session)
    return {
        "message": "Pipeline executed successfully",
        "processed": counter,
    }

@router.get("/api/v1/hospitals")
async def list_hospitals(page: int = 1, limit: int = 20, state: str | None = None, search: str | None = None, session: AsyncSession = Depends(get_session)):
    return await get_hospitals(session, page, limit, state, search)

@router.get("/api/v1/hospitals/{facility_id}")
async def get_hospitals_facility_id(facility_id: str, session: AsyncSession = Depends(get_session)):
    hospital = await get_hospitals_by_id(session, facility_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital

@router.post("/api/v1/ai/query")
@limiter.limit("5/minute")
async def ai_query(request: Request, body: AIQueryRequest, session: AsyncSession = Depends(get_session)):
    return await ask_hospital_ai(session, body.question)

@router.post("/api/v1/pipeline/run/infections")
async def run_infections_pipeline(session: AsyncSession = Depends(get_session)):
    counter = await ingest_infections(session)
    return{
        "message": "Infections pipeline executed successfully",
        "processed": counter,
    }
    
@router.get("/api/v1/infections")
async def list_infections(
    state: str | None = None,
    compared_to_national: str | None = None,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    return await get_infections(session, state, compared_to_national, page, limit)

@router.get("/api/v1/infections/{facility_id}")
async def get_facility_infections(facility_id: str, session: AsyncSession = Depends(get_session)):
    infections = await get_infections_by_facility(session, facility_id)
    if not infections:
        raise HTTPException(status_code=404, detail="No infection data found for this facility")
    return infections

@router.get("/api/v1/hospitals/metrics/rating-distribution")
async def rating_distribution(session: AsyncSession = Depends(get_session)):
    return await get_rating_distribution(session)