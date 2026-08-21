from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.ai.hospital_ai_service import ask_hospital_ai

router = APIRouter()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
        
class AIQueryRequest(BaseModel):
    question: str
    
@router.post("/api/v1/ai/query")
async def ai_query(request: AIQueryRequest, session: AsyncSession = Depends(get_session),):
    return await ask_hospital_ai(session, request.question)