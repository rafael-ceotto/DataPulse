from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.hospital_service import ingest_hospitals
from app.repositories.hospital_repository import get_hospitals, get_hospitals_by_id, save_hospitals

router = APIRouter()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
        
@router.post("/api/v1/pipeline/run")
async def run_pipeline(session: AsyncSession = Depends(get_session),
):
    counter = await ingest_hospitals(session)
    return{
        "message":"Pipeline executed successfully",
        "processed": counter,
    }
    
@router.get("/api/v1/hospitals")
async def list_hospitals(page: int =1, limit: int=20, state: str | None = None, session: AsyncSession = Depends(get_session)):
    return await get_hospitals(session, page, limit, state)

@router.get("/api/v1/hospitals/{facility_id}")
async def get_hospitals_facility_id(facility_id: str, session: AsyncSession = Depends(get_session)):
    hospital = await get_hospitals_by_id(session, facility_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital