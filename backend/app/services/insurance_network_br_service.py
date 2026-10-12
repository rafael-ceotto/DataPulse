import os
import zipfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital
from app.pipeline.insurance_network_br_ingestion import download_ans_zip, parse_state_csv
from app.repositories.insurance_network_br_repository import save_insurance_network_entries


async def ingest_br_insurance_network(session: AsyncSession) -> dict:
    result = await session.execute(
        select(Hospital.facility_id).where(Hospital.country == "BR")
    )
    cnes_to_facility_id = {
        row[0].removeprefix("BR-"): row[0] for row in result.all()
    }

    zip_path = await download_ans_zip()
    stats = {}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for entry_name in zf.namelist():
                dedup = parse_state_csv(zf, entry_name, cnes_to_facility_id)
                saved = await save_insurance_network_entries(session, list(dedup.values()))
                stats[entry_name] = saved
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    return stats