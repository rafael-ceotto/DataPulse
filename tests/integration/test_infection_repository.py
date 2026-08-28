from app.models.infection import HospitalInfection as InfectionModel
from app.models.hospital import Hospital as HospitalModel
from app.repositories.infection_repository import get_infections, get_infections_by_facility
from sqlalchemy import insert


async def create_hospital(session, facility_id: str, state: str = "MA"):
    await session.execute(
        insert(HospitalModel).values(
            facility_id=facility_id,
            facility_name=f"Hospital {facility_id}",
            address="123 Main St",
            city="Boston",
            state=state,
            zip_code="02108",
            hospital_type="Acute Care Hospitals",
            hospital_ownership="Voluntary non-profit - Private",
            emergency_services="Yes",
            overall_rating=4,
            telephone_number="555-1234",
        )
    )
    await session.commit()


async def create_infection(session, facility_id: str, state: str = "MA"):
    await session.execute(
        insert(InfectionModel).values(
            facility_id=facility_id,
            facility_name=f"Hospital {facility_id}",
            state=state,
            measure_id="HAI_1_SIR",
            measure_name="CLABSI",
            compared_to_national="No Different than the National Benchmark",
            score=None,
            start_date=None,
            end_date=None,
        )
    )
    await session.commit()


async def test_get_infections(test_session):
    await create_hospital(test_session, "INF001", state="MA")
    await create_hospital(test_session, "INF002", state="MA")
    await create_infection(test_session, "INF001", state="MA")
    await create_infection(test_session, "INF002", state="MA")

    result = await get_infections(test_session, state=None, compared_to_national=None, page=1, limit=10)
    assert isinstance(result, list)
    assert len(result) >= 2


async def test_get_infections_filter_by_state(test_session):
    await create_hospital(test_session, "INF003", state="TX")
    await create_infection(test_session, "INF003", state="TX")

    result = await get_infections(test_session, state="TX", compared_to_national=None, page=1, limit=10)
    assert all(i.state == "TX" for i in result)


async def test_get_infections_by_facility(test_session):
    await create_hospital(test_session, "INF004", state="CA")
    await create_infection(test_session, "INF004", state="CA")

    result = await get_infections_by_facility(test_session, "INF004")
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].facility_id == "INF004"


async def test_get_infections_by_facility_not_found(test_session):
    result = await get_infections_by_facility(test_session, "DOES_NOT_EXIST")
    assert result == [] or result is None