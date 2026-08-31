from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.cms_ingestion import fetch_data_cms, parse_hospitals
from app.repositories.hospital_repository import save_hospitals
from app.repositories.pipeline_run_repository import create_pipeline_run, update_pipeline_run, get_previous_avg_rating, get_recent_insights
from app.ai.insight_service import generate_insight


async def ingest_hospitals(session: AsyncSession):
    pipeline_run = await create_pipeline_run(session)
    try:
        csv_text = await fetch_data_cms()
        if csv_text is None:
            raise ValueError("Failed to fetch data from CMS")

        hospitals = parse_hospitals(csv_text)
        await save_hospitals(session, hospitals)

        rated = [h.overall_rating for h in hospitals if h.overall_rating is not None]
        avg_rating = round(sum(rated) / len(rated), 2) if rated else None
        
        # Generate Insight
        insight = None
        if avg_rating is not None:
            try:
                print(f"=== INSIGHT: generating for avg_rating={avg_rating} ===")
                previous_avg = await get_previous_avg_rating(session)
                print(f"=== INSIGHT: previous_avg={previous_avg} ===")
                history = await get_recent_insights(session, limit=5)
                print(f"=== INSIGHT: history={len(history)} items ===")
                insight = await generate_insight(avg_rating, previous_avg, history)
                print(f"=== INSIGHT: generated={insight[:50]} ===")
            except Exception as e:
                print(f"Insight heneration failed: {e}")

        await update_pipeline_run(
            session,
            pipeline_run,
            status="success",
            records_received=len(hospitals),
            records_processed=len(hospitals),
            records_failed=0,
            avg_rating=avg_rating,
            insight=insight,
            
        )
        return len(hospitals)

    except Exception as e:
        await update_pipeline_run(
            session,
            pipeline_run,
            status="failed",
            records_received=0,
            records_processed=0,
            records_failed=0,
            error_message=str(e),
        )
        raise