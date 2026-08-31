from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio

from app.models.hospital import Hospital as HospitalModel
from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache, set_cache, invalidate_cache
from app.core.auth import get_current_user
from app.services.hospital_service import ingest_hospitals
from app.repositories.hospital_repository import get_hospitals, get_hospitals_by_id, save_hospitals, get_rating_distribution
from app.ai.hospital_ai_service import ask_hospital_ai
from app.services.infection_service import ingest_infections
from app.repositories.infection_repository import get_infections, get_infections_by_facility
from app.services.physician_analysis_service import get_physician_hospital_correlation, search_physicians, get_scarce_specialties
from app.ai.hospital_agent_service import ask_agent
from app.repositories.pipeline_run_repository import get_pipeline_runs

import hashlib


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

class AIQueryRequest(BaseModel):
    question: str

@router.post("/api/v1/pipeline/run")
async def run_pipeline(session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    counter = await ingest_hospitals(session)
    await invalidate_cache("rating_distribution")
    await invalidate_cache("ai_query:*")
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
async def ai_query(request: Request, body: AIQueryRequest, session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    cache_key = f"ai_query:{hashlib.md5(body.question.lower().encode()).hexdigest()}"
    cached = await get_cache(cache_key)
    if cached:
        return cached
    result = await ask_agent(session, body.question)
    await set_cache(cache_key, result, ttl=600)
    return result

@router.post("/api/v1/pipeline/run/infections")
async def run_infections_pipeline(session: AsyncSession = Depends(get_session), current_user: dict = Depends(get_current_user)):
    counter = await ingest_infections(session)
    return {
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
    cache_key = "rating_distribution"
    cached = await get_cache(cache_key)
    if cached:
        return cached
    data = await get_rating_distribution(session)
    await set_cache(cache_key, data, ttl=3600)
    return data

@router.get("/api/v1/physicians")
async def list_physicians(
    state: str | None = None,
    specialty: str | None = None,
    name: str | None = None,
    limit: int = 20
):
    return await search_physicians(state=state, specialty=specialty, name=name, limit=limit)

@router.get("/api/v1/physicians/correlation")
async def physician_hospital_correlation(session: AsyncSession = Depends(get_session)):
    cache_key = "physician_hospital_correlation"
    cached = await get_cache(get_session)
    if cached:
        return cached
    data = await get_physician_hospital_correlation(session)
    await set_cache(cache_key, data, ttl=86400)
    return data

@router.get("/api/v1/physicians/state-analysis/{state}")
async def physician_state_analysis(state: str, session: AsyncSession = Depends(get_session)):
    cache_key = f"physician_state_analysis: {state}"
    cached = await get_cache(cache_key)
    if cached:
        return cached
    
    # On-demand physician search per state
    physician_data = await search_physicians(state=state, limit=1)
    physician_count = physician_data.get("total", 0)
    
    # Hospital data search from DB
    result = await session.execute(
        select(
            func.avg(HospitalModel.overall_rating).label("avg_rating"),
            func.count(HospitalModel.facility_id).label("hospital_count"),
        )
        .where(HospitalModel.state == state)
        .where(HospitalModel.overall_rating.isnot(None))
    )
    row = result.first()
    
    data = {
        "state": state,
        "physician_count": physician_count,
        "hospital_count": row.hospital_count if row else 0,
        "avg_hospital_rating": round(float(row.avg_rating), 2) if row and row.avg_rating else None,
        "physicians_per_hospital": round(physician_count / row.hospital_count, 1) if row and row.hospital_count else None,
     }
    
    await set_cache(cache_key, data, ttl=3600)
    return data

@router.get("/api/v1/physicians/scarce-specialties/{state}")
async def scarce_specialties(state: str):
    return await get_scarce_specialties(state)

@router.post("/api/v1/physicians/warm-cache")
async def warm_physician_cache():
    """
    Triggers background population of national specialty counts cache.
    Returns immediately — cache builds in background.
    Check Redis key 'national_specialty_counts' to verify completion.
    """
    from app.services.physician_analysis_service import get_national_specialty_counts
    asyncio.create_task(get_national_specialty_counts())
    return {
        "message": "Cache warming started in background",
        "note": "Call /api/v1/physicians/scarce-specialties/{state} after cache is ready"
    }
    
@router.get("/api/v1/physicians/cache-status")
async def physician_cache_status():
    from app.services.physician_analysis_service import NATIONAL_SPECIALTY_CACHE_KEY
    national = await get_cache(NATIONAL_SPECIALTY_CACHE_KEY)
    return {
        "national_specialty_cache": "ready" if national else "not_ready",
        "specialties_cached": len(national) if national else 0,
    }
    
@router.get("/api/v1/pipeline/runs")
async def list_pipeline_runs(limit: int=20, session: AsyncSession = Depends(get_session)):
    runs = await get_pipeline_runs(session, limit)
    return [
        {
          "id": str(r.id),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "status": r.status,
            "records_received": r.records_received,
            "records_processed": r.records_processed,
            "records_failed": r.records_failed,
            "error_message": r.error_message,
            "avg_rating": r.avg_rating,
            "duration_seconds": round((r.finished_at - r.started_at).total_seconds(), 1) if r.finished_at and r.started_at else None,
            
        }
        for r in runs
    ]