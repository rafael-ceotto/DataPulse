from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import Hospital
from app.models.insurance import HospitalEnrollment as EnrollmentModel
from app.schemas.insurance import HospitalEnrollment as EnrollmentSchema


async def save_enrollments(session: AsyncSession, enrollments: list[EnrollmentSchema]) -> int:
    existing_ids_result = await session.execute(select(Hospital.facility_id))
    existing_ids = {row[0] for row in existing_ids_result.all()}

    saved_count = 0
    try:
        for enrollment in enrollments:
            if enrollment.facility_id not in existing_ids:
                continue

            stmt = insert(EnrollmentModel).values(
                facility_id=enrollment.facility_id,
                npi=enrollment.npi,
                organization_name=enrollment.organization_name,
                enrollment_state=enrollment.enrollment_state,
                proprietary_nonprofit=enrollment.proprietary_nonprofit,
                is_acute_care=enrollment.is_acute_care,
                is_psychiatric=enrollment.is_psychiatric,
                is_rehabilitation=enrollment.is_rehabilitation,
                is_childrens=enrollment.is_childrens,
                is_long_term=enrollment.is_long_term,
                is_swing_bed=enrollment.is_swing_bed,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["facility_id"],
                set_={
                    "npi": stmt.excluded.npi,
                    "organization_name": stmt.excluded.organization_name,
                    "enrollment_state": stmt.excluded.enrollment_state,
                    "proprietary_nonprofit": stmt.excluded.proprietary_nonprofit,
                    "is_acute_care": stmt.excluded.is_acute_care,
                    "is_psychiatric": stmt.excluded.is_psychiatric,
                    "is_rehabilitation": stmt.excluded.is_rehabilitation,
                    "is_childrens": stmt.excluded.is_childrens,
                    "is_long_term": stmt.excluded.is_long_term,
                    "is_swing_bed": stmt.excluded.is_swing_bed,
                },
            )
            await session.execute(stmt)
            saved_count += 1
        await session.commit()
        return saved_count
    except SQLAlchemyError as e:
        await session.rollback()
        raise e

async def get_enrollment_by_facility(session: AsyncSession, facility_id: str) -> EnrollmentModel | None:
    result = await session.execute(
        select(EnrollmentModel).where(EnrollmentModel.facility_id == facility_id)
    )
    return result.scalar_one_or_none()

async def get_enrollments(session: AsyncSession, state: str | None = None, hospital_type: str | None = None, page: int = 1, limit: int = 20) -> list[EnrollmentModel]:
    query = select(EnrollmentModel)
    if state:
        query = query.where(EnrollmentModel.enrollment_state == state)
    if hospital_type == "acute_care":
        query = query.where(EnrollmentModel.is_acute_care.is_(True))
    elif hospital_type == "psychiatric":
        query = query.where(EnrollmentModel.is_psychiatric.is_(True))
    elif hospital_type == "rehabilitation":
        query = query.where(EnrollmentModel.is_rehabilitation.is_(True))
    elif hospital_type == "childrens":
        query = query.where(EnrollmentModel.is_childrens.is_(True))
    elif hospital_type == "long_term":
        query = query.where(EnrollmentModel.is_long_term.is_(True))
    elif hospital_type == "swing_bed":
        query = query.where(EnrollmentModel.is_swing_bed.is_(True))
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()