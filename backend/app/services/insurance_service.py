from sqlalchemy.ext.asyncio import AsyncSession
from app.pipeline.enrollment_ingestion import fetch_enrollment_cms, parse_enrollment
from app.repositories.insurance_repository import save_enrollments

async def ingest_enrollments(session: AsyncSession) -> int:
    csv_text = await fetch_enrollment_cms()
    if csv_text is None:
        raise ValueError("Failed to fetch enrollment data from CMS")
    enrollments = parse_enrollment(csv_text)
    saved_count =await save_enrollments(session, enrollments)
    return saved_count