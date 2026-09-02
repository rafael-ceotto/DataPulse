from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
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


async def get_hospitals(session: AsyncSession, page: int = 1, limit: int = 20, state: str | None = None, search: str | None = None, min_rating: int | None = None) -> list[HospitalModel]:
    query = select(HospitalModel)
    if state:
        query = query.where(HospitalModel.state == state)
    if min_rating is not None:
        query = query.where(HospitalModel.overall_rating >= min_rating)
    if search:
        query = query.where(
            func.similarity(HospitalModel.facility_name, search) > 0.1
        ).order_by(
            func.similarity(HospitalModel.facility_name, search).desc()
        )
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()

async def get_hospitals_by_id(session: AsyncSession, facility_id: str) -> HospitalModel | None:
    result = await session.execute(select(HospitalModel).where(HospitalModel.facility_id == facility_id))
    return result.scalar_one_or_none()

async def get_rating_distribution(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(
            HospitalModel.state,
            func.avg(HospitalModel.overall_rating).label("avg_rating"),
            func.count(HospitalModel.facility_id).label("total",)
        )
        .where(HospitalModel.overall_rating.isnot(None))
        .group_by(HospitalModel.state)
        .order_by(func.avg(HospitalModel.overall_rating).desc())
    )
    return [{"state": r.state, "avg_rating": round(float(r.avg_rating), 2), "total": r.total} for r in result]

async def get_all_hospitals_by_state(session: AsyncSession, state: str) -> list[HospitalModel]:
    result = await session.execute(
        select(HospitalModel).where(HospitalModel.state == state).order_by(HospitalModel.facility_name)
    )
    return result.scalars().all()

async def get_data_quality_metrics(session: AsyncSession) -> dict:
    total_result =  await session.execute(
        select(func.count(HospitalModel.facility_id))
    )
    total = total_result.scalar()
    
    rated_result = await session.execute(
        select(func.count(HospitalModel.facility_id)).where(HospitalModel.overall_rating.isnot(None))
    )
    rated = rated_result.scalar()
    
    low_result = await session.execute(
        select(func.count(HospitalModel.facility_id)).where(HospitalModel.overall_rating <=2).where(HospitalModel.overall_rating.isnot(None))
    )
    low_rated = low_result.scalar()
    
    no_phone_result = await session.execute(
        select(HospitalModel.facility_id).where(HospitalModel.telephone_number.is_(None))
    )
    no_phone = no_phone_result.scalar()
    
    return {
       "total_hospitals": total,
        "rated_hospitals": rated,
        "unrated_hospitals": total - rated,
        "completeness_pct": round((rated / total) * 100, 1) if total else 0,
        "low_rated_hospitals": low_rated,
        "missing_phone": no_phone, 
    }