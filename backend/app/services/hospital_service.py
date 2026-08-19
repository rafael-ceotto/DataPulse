from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.cms_ingestion import fetch_data_cms, parse_hospitals
from app.repositories.hospital_repository import save_hospitals
from app.repositories.pipeline_run_repository import create_pipeline_run, update_pipeline_run

async def ingest_hospitals(session: AsyncSession):
    pipeline_run = await create_pipeline_run(session)
    try:
        csv_text = await fetch_data_cms()
        if csv_text is None:
         raise ValueError("Failed to fetch data from CMS")
        hospitals = parse_hospitals(csv_text)
    
        await save_hospitals(session, hospitals)
    
        await update_pipeline_run(
        session, pipeline_run, status="success", records_received=len(hospitals), records_processed=len(hospitals), records_failed=0,
    )
        return len(hospitals)

    except Exception as e:
        await update_pipeline_run(session, pipeline_run, status="failed", records_received=0, records_processed=0, records_failed=0, error_message=str(e))
        raise