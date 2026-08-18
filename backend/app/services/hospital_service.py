from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.cms_ingestion import fetch_data_cms, parse_hospitals
from app.repositories.hospital_repository import save_hospitals

async def ingest_hospitals(session: AsyncSession):
    csv_text = await fetch_data_cms()
    if csv_text is None:
        raise ValueError("Failed to fetch data from CMS")
    hospitals = parse_hospitals(csv_text)
    await save_hospitals(session, hospitals)
    
    return len(hospitals)