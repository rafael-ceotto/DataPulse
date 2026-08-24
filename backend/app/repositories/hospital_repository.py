from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.hospital import Hospital as HospitalModel
from app.schemas.hospital import Hospital as HospitalSchema


async def save_hospitals(session: AsyncSession,
                         hospitals: list[HospitalSchema]) -> None:
    try:
        for hospital in hospitals:
            stmt = insert(HospitalModel).values(
                facility_id=hospital.facility_id,
                facility_name=hospital.facility_name,
                address=hospital.address,
                city=hospital.city,
                state=hospital.state,
                zip_code=hospital.zip_code,
                hospital_type=hospital.hospital_type,
                hospital_ownership=hospital.hospital_ownership,
                emergency_services=hospital.emergency_services,
                overall_rating=hospital.overall_rating,
                telephone_number=hospital.telephone_number,
            ).on_conflict_do_update(
                index_elements=["facility_id"],
                set_=dict(
                    facility_name=hospital.facility_name,
                    overall_rating=hospital.overall_rating,
                    hospital_ownership=hospital.hospital_ownership,
                    telephone_number=hospital.telephone_number
                )
            )
            await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


async def get_hospitals(session: AsyncSession, page: int = 1, limit: int = 20, state: str | None = None, search: str | None = None) -> list[HospitalModel]:
    query = select(HospitalModel)
    if state:
        query = query.where(HospitalModel.state == state)
    if search:
        query = query.where(HospitalModel.facility_name.ilike(f"%{search}%"))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_hospitals_by_id(session: AsyncSession, facility_id: str) -> HospitalModel | None:
    result = await session.execute(select(HospitalModel).where(HospitalModel.facility_id == facility_id))
    return result.scalar_one_or_none()