from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_run import PipelineRun

async def create_pipeline_run(session: AsyncSession) -> PipelineRun:
    pipeline_run = PipelineRun(
        started_at = datetime.now(timezone.utc),
        status = "running",
        records_received = 0,
        records_processed = 0,
        records_failed = 0,
    )
    session.add(pipeline_run)
    await session.commit()
    await session.refresh(pipeline_run)
    return pipeline_run

async def update_pipeline_run(
    session: AsyncSession, 
    pipeline_run: PipelineRun, 
    status: str, 
    records_received: int,
    records_processed: int, 
    records_failed: int, 
    error_message: str | None = None,
):
    pipeline_run.finished_at = datetime.now(timezone.utc)
    pipeline_run.status = status
    pipeline_run.records_received = records_received
    pipeline_run.records_processed = records_processed
    pipeline_run.records_failed = records_failed
    pipeline_run.error_message = error_message
    
    await session.commit()
    
async def get_pipeline_runs(session: AsyncSession, limit: int=20) -> list[PipelineRun]:
    from sqlalchemy import select
    result = await session.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    )
    return result.scalars().all()