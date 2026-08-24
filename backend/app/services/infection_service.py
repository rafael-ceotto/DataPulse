from sqlalchemy.ext.asyncio import AsyncSession

from app.pipeline.infections_ingestion import fetch_infections_cms, parse_infections
from app.repositories.infection_repository import save_infections

async def ingest_infections(session: AsyncSession) -> int:
    csv_text = await fetch_infections_cms()
    if csv_text is None:
        raise ValueError("Failed to fetch infection data from CMS")
    infections = parse_infections(csv_text)
    await save_infections(session, infections)
    return len(infections)