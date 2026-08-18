from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.hospital_service import ingest_hospitals

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