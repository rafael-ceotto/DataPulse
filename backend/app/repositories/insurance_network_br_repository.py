from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.insurance_br import HospitalInsuranceNetwork as NetworkModel
from app.schemas.insurance_br import HospitalInsuranceNetworkEntry

BATCH_SIZE = 2000


async def save_insurance_network_entries(session: AsyncSession, entries: list[HospitalInsuranceNetworkEntry]) -> int:
    if not entries:
        return 0

    try:
        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i:i + BATCH_SIZE]
            values = [
                {
                    "facility_id": e.facility_id,
                    "operator_code": e.operator_code,
                    "operator_name": e.operator_name,
                    "has_emergency_coverage": e.has_emergency_coverage,
                    "coverage_type": e.coverage_type,
                    "provider_relationship": e.provider_relationship,
                    "is_active": e.is_active,
                }
                for e in batch
            ]
            stmt = insert(NetworkModel).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["facility_id", "operator_code"],
                set_={
                    "operator_name": stmt.excluded.operator_name,
                    "has_emergency_coverage": stmt.excluded.has_emergency_coverage,
                    "coverage_type": stmt.excluded.coverage_type,
                    "provider_relationship": stmt.excluded.provider_relationship,
                    "is_active": stmt.excluded.is_active,
                },
            )
            await session.execute(stmt)
        await session.commit()
        return len(entries)
    except SQLAlchemyError:
        await session.rollback()
        raise


async def get_insurance_network_by_facility(session: AsyncSession, facility_id: str) -> list[NetworkModel]:
    result = await session.execute(
        select(NetworkModel)
        .where(NetworkModel.facility_id == facility_id)
        .where(NetworkModel.is_active.is_(True))
    )
    return result.scalars().all()