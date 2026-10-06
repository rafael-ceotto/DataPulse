import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert

from app.models.hospital import Hospital as HospitalModel
from app.schemas.hospital import Hospital as HospitalSchema

CITY_FILTER_COUNTRIES = {"IT", "ES", "PT", "BE", "CA", "MT", "GB", "FR"}

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
                latitude=hospital.latitude,
                longitude=hospital.longitude,
                country=hospital.country,
                normalized_score=hospital.normalized_score,
                rating_system=hospital.rating_system,
                raw_rating_label=hospital.raw_rating_label,
            ).on_conflict_do_update(
                index_elements=["facility_id"],
                set_=dict(
                    facility_name=hospital.facility_name,
                    address=hospital.address,
                    city=hospital.city,
                    hospital_ownership=hospital.hospital_ownership,
                    emergency_services=hospital.emergency_services,
                    zip_code=hospital.zip_code,
                    overall_rating=hospital.overall_rating,
                    telephone_number=hospital.telephone_number,
                    latitude=hospital.latitude,
                    longitude=hospital.longitude,
                    country=hospital.country,
                    normalized_score=hospital.normalized_score,
                    rating_system=hospital.rating_system,
                    raw_rating_label=hospital.raw_rating_label,
                )
            )
            await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


async def get_hospitals(
    session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    state: str | None = None,
    search: str | None = None,
    min_rating: int | None = None,
    max_rating: int | None = None,
    country: str | None = "US"
) -> list[HospitalModel]:
    query = select(HospitalModel)
    if country:
        query = query.where(HospitalModel.country == country)
    if state:
        if country in CITY_FILTER_COUNTRIES:
            query = query.where(HospitalModel.city.ilike(f"%{state}%"))
        else:
            query = query.where(HospitalModel.state == state)
    if min_rating is not None:
        query = query.where(HospitalModel.overall_rating >= min_rating)
    if max_rating is not None:
        query = query.where(HospitalModel.overall_rating <= max_rating)
    if search:
        if len(search) < 3:
            query = query.where(HospitalModel.facility_name.ilike(f"%{search}%"))
        else:
            query = query.where(
                func.similarity(HospitalModel.facility_name, search) > 0.1
            ).order_by(
                func.similarity(HospitalModel.facility_name, search).desc()
            )
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_hospitals_by_id(session: AsyncSession, facility_id: str) -> HospitalModel | None:
    result = await session.execute(
        select(HospitalModel).where(HospitalModel.facility_id == facility_id)
    )
    return result.scalar_one_or_none()


async def get_rating_distribution(session: AsyncSession, country: str = "US") -> list[dict]:
    result = await session.execute(
        select(
            HospitalModel.state,
            func.avg(HospitalModel.overall_rating).label("avg_rating"),
            func.count(HospitalModel.facility_id).label("total")
        )
        .where(HospitalModel.overall_rating.isnot(None))
        .where(HospitalModel.country == country)
        .group_by(HospitalModel.state)
        .order_by(func.avg(HospitalModel.overall_rating).desc())
    )
    return [{"state": r.state, "avg_rating": round(float(r.avg_rating), 2), "total": r.total} for r in result]


async def get_all_hospitals_by_state(session: AsyncSession, state: str) -> list[HospitalModel]:
    result = await session.execute(
        select(HospitalModel).where(HospitalModel.state == state).order_by(HospitalModel.facility_name)
    )
    return result.scalars().all()


async def get_data_quality_metrics(session: AsyncSession, country: str = "US") -> dict:
    total_result = await session.execute(
        select(func.count(HospitalModel.facility_id)).where(HospitalModel.country == country)
    )
    total = total_result.scalar()

    rated_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.overall_rating.isnot(None))
        .where(HospitalModel.country == country)
    )
    rated = rated_result.scalar()

    low_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.overall_rating <= 2)
        .where(HospitalModel.overall_rating.isnot(None))
        .where(HospitalModel.country == country)
    )
    low_rated = low_result.scalar()

    no_phone_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.telephone_number.is_(None))
        .where(HospitalModel.country == country)
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


async def get_hospitals_nearby(
    session: AsyncSession,
    lat: float,
    lng: float,
    radius_miles: float = 50.0,
    min_rating: int | None = None,
    limit: int = 20,
    country: str = "US"
) -> list[dict]:
    lat_delta = radius_miles / 69.0
    lng_delta = radius_miles / (69.0 * abs(math.cos(math.radians(lat))))
    query = (
        select(
            HospitalModel,
            (
                func.sqrt(
                    func.pow((HospitalModel.latitude - lat) * 69, 2) +
                    func.pow((HospitalModel.longitude - lng) * 69 * func.cos(func.radians(lat)), 2)
                )
            ).label("distance_miles")
        )
        .where(HospitalModel.latitude.isnot(None))
        .where(HospitalModel.longitude.isnot(None))
        .where(HospitalModel.latitude.between(lat - lat_delta, lat + lat_delta))
        .where(HospitalModel.longitude.between(lng - lng_delta, lng + lng_delta))
        .where(HospitalModel.country == country)
    )
    if min_rating is not None:
        query = query.where(HospitalModel.overall_rating >= min_rating)
    query = query.order_by(text("distance_miles")).limit(limit)

    result = await session.execute(query)
    rows = result.all()

    return [
        {
            "facility_id": h.facility_id,
            "facility_name": h.facility_name,
            "city": h.city,
            "state": h.state,
            "address": h.address,
            "zip_code": h.zip_code,
            "hospital_type": h.hospital_type,
            "emergency_services": h.emergency_services,
            "overall_rating": h.overall_rating,
            "telephone_number": h.telephone_number,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "distance_miles": round(distance, 1),
        }
        for h, distance in rows
        if distance <= radius_miles
    ]


async def get_total_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(HospitalModel.facility_id)))
    return result.scalar()

async def get_all_hospitals_by_filter(
    session: AsyncSession,
    state: str | None = None,
    city: str | None = None,
    country: str = "US",
) -> list[HospitalModel]:
    query = select(HospitalModel).where(HospitalModel.country == country)
    if city:
        query = query.where(HospitalModel.city.ilike(f"%{city}%"))
    elif state:
        query = query.where(HospitalModel.state == state)
    query = query.order_by(HospitalModel.facility_name)
    result = await session.execute(query)
    return result.scalars().all()

async def get_country_stats(session: AsyncSession, country: str) -> dict:
    total_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.country == country)
    )
    total = total_result.scalar()
    
    emergency_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.country == country)
        .where(HospitalModel.emergency_services.in_(["Yes", "Sim"]))
    )
    emergency = emergency_result.scalar()
    
    phone_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.country == country)
        .where(HospitalModel.telephone_number.isnot(None))
    )
    with_phone = phone_result.scalar()

    coords_result = await session.execute(
        select(func.count(HospitalModel.facility_id))
        .where(HospitalModel.country == country)
        .where(HospitalModel.latitude.isnot(None))
    )
    with_coords = coords_result.scalar()
    
    type_result = await session.execute(
        select(func.count(func.distinct(HospitalModel.hospital_type)))
        .where(HospitalModel.country == country)
        .where(HospitalModel.hospital_type != "")
    )
    type_count = type_result.scalar()

    return {
        "country": country,
        "total": total,
        "with_emergency": emergency,
        "with_phone": with_phone,
        "with_coords": with_coords,
        "type_count": type_count,
    }