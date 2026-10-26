import json
from app.core.cache import get_cache, set_cache
from app.core.logging import logger

JOB_TTL = 3600

async def create_job(job_id: str, question: str, country: str = "US", conversation_id: str | None = None) -> None:
    await set_cache(f"job:{job_id}", {
        "job_id": job_id,
        "question": question,
        "country": country,
        "conversation_id": conversation_id,
        "status": "queued",
        "result": None,
    }, ttl=JOB_TTL)
    logger.info("job_created", job_id=job_id)
    
async def set_job_processing(job_id: str) -> None:
    job = await get_cache(f"job:{job_id}")
    if job:
        job["status"] = "processing"
        await set_cache(f"job:{job_id}", job, ttl=JOB_TTL)
        logger.info("job_processing", job_id=job_id)
        
async def set_job_done(job_id: str, result: dict) -> None:
    job =  await get_cache(f"job:{job_id}")
    if job:
        job["status"] = "done"
        job["result"] = result
        await set_cache(f"job:{job_id}", job, ttl=JOB_TTL)
        logger.info("job_done", job_id=job_id)
        
async def set_job_failed(job_id: str, error: dict) -> None:
    job =  await get_cache(f"job:{job_id}")
    if job:
        job["status"] = "failed"
        job["error"] = error
        await set_cache(f"job:{job_id}", job, ttl=JOB_TTL)
        logger.error("job_failed", job_id=job_id, error=error)
        
async def get_job(job_id: str) -> dict | None:
    return await get_cache(f"job:{job_id}")
        
