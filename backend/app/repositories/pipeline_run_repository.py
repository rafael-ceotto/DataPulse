from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_run import PipelineRun


async def create_pipeline_run(session: AsyncSession) -> PipelineRun:
    pipeline_run = PipelineRun(
        started_at=datetime.now(timezone.utc),
        status="running",
        records_received=0,
        records_processed=0,
        records_failed=0,
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
    avg_rating: float | None = None,
    insight: str | None = None,
):
    pipeline_run.finished_at = datetime.now(timezone.utc)
    pipeline_run.status = status
    pipeline_run.records_received = records_received
    pipeline_run.records_processed = records_processed
    pipeline_run.records_failed = records_failed
    pipeline_run.error_message = error_message
    pipeline_run.avg_rating = avg_rating
    pipeline_run.insight = insight

    await session.commit()


async def get_pipeline_runs(session: AsyncSession, limit: int = 20) -> list[PipelineRun]:
    result = await session.execute(
        select(PipelineRun)
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_recent_insights(session: AsyncSession, limit: int = 5) -> list[dict]:
    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.status == "success")
        .where(PipelineRun.avg_rating.isnot(None))
        .where(PipelineRun.insight.isnot(None))
        .order_by(PipelineRun.started_at.desc())
        .limit(limit)
    )
    runs = result .scalars().all()
    return[
        {
            "started_at": r.started_at.isoformat(),
            "avg_rating": r.avg_rating,
            "insight": r.insight,   
        }
        for r in reversed(runs)
    ]
    
async def get_previous_avg_rating(session: AsyncSession) -> float | None:
    result = await session.execute(
        select(PipelineRun)
        .where(PipelineRun.status == "success")
        .where(PipelineRun.avg_rating.isnot(None))
        .order_by(PipelineRun.started_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    return run.avg_rating if run else None