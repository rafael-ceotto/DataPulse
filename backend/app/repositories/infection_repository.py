from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.infection import HospitalInfection as InfectionModel
from app.schemas.infection import HospitalInfection as InfectionSchema

async def save_infections(session: AsyncSession, infections: list[InfectionSchema]) -> None:
    try:
        for infection in infections:
            stmt = insert(InfectionModel).values(
                facility_id=infection.facility_id,
                facility_name=infection.facility_name,
                state=infection.state,
                measure_id=infection.measure_id,
                measure_name=infection.measure_name,
                compared_to_national=infection.compared_to_national,
                score=infection.score,
                start_date=infection.start_date,
                end_date=infection.end_date,
            ).on_conflict_do_nothing()
            await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    
async def get_infections_by_facility(session: AsyncSession, facility_id:str) ->[InfectionModel]:
    result = await session.execute(
        select(InfectionModel).where(InfectionModel.facility_id == facility_id)
    )
    return result.scalars().all()

async def get_infections(session: AsyncSession, state: str | None = None, compared_to_national: str | None = None, page: int = 1, limit: int = 20) -> list[InfectionModel]:
    query = select(InfectionModel)
    if state:
        query = query.where(InfectionModel.state == state)
    if compared_to_national:
        query = query.where(InfectionModel.compared_to_national == compared_to_national)
    query = query.offset((page - 1) * limit).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()