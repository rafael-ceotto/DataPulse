from app.models.hospital import Hospital as HospitalModel
from app.repositories.hospital_repository import get_hospitals_by_id, get_hospitals, save_hospitals, get_all_hospitals_by_state, get_data_quality_metrics
from app.schemas.hospital import Hospital

from sqlalchemy import select

def create_hospital(facility_id: str) -> Hospital:
    return Hospital(
        facility_id=facility_id,
        facility_name=f"Hospital {facility_id}",
        address="123 Main St",
        city="Boston",
        state="MA",
        zip_code="02108",
        hospital_type="Acute Care Hospitals",
        hospital_ownership="Voluntary non-profit - Private",
        emergency_services="Yes",
        overall_rating=4,
        telephone_number="555-1234",
    )
    
async def test_save_hospitals(test_session):
    hospitals=[
        create_hospital("000001"),
        create_hospital("000002"),
    ]
    await save_hospitals(test_session, hospitals)
    result = await test_session.execute(
        select(HospitalModel)
    )
    saved = result.scalars().all()
    assert len(saved) == 2
    
async def test_get_hospitals(test_session):
    hospitals=[
        create_hospital("000001"),
        create_hospital("000002"),
        create_hospital("000003"),
    ]
    await save_hospitals(test_session, hospitals)
    result = await get_hospitals(test_session, page=1, limit=2)
    assert len(result) == 2
    
async def test_get_hospital_by_id(test_session):
    hospitals = [create_hospital("000001")]
    await save_hospitals(test_session, hospitals)
    result = await get_hospitals_by_id(test_session, "000001")
    assert result is not None
    assert result.facility_id == "000001"
    assert result.facility_name == "Hospital 000001"
    
async def test_get_hospital_by_id_not_found(test_session):
    result = await get_hospitals_by_id(test_session, "does-not-exist")
    assert result is None
    
async def test_get_all_hospitals_by_state(test_session):
    hospitals=[
        create_hospital("000001"),
        create_hospital("000002"),
        create_hospital("000003"),
    ]
    await save_hospitals(test_session, hospitals)
    result = await get_all_hospitals_by_state(test_session, "MA")
    assert isinstance(result, list)
    assert len(result) >= 3
    assert all(h.state == "MA" for h in result)
    
async def test_get_all_hospitals_by_state_empty(test_session):
     result = await get_all_hospitals_by_state(test_session, "ZZ")
     assert result == []
     
async def test_get_data_quality_metrics(test_session):
    hospitals = [
        create_hospital("000001"),
        create_hospital("000002"),
    ]
    await save_hospitals(test_session, hospitals)
    result = await get_data_quality_metrics(test_session)
    assert "total_hospitals" in result
    assert "rated_hospitals" in result
    assert "unrated_hospitals" in result
    assert "completeness_pct" in result
    assert "low_rated_hospitals" in result
    assert result["total_hospitals"] >= 2
    assert result["completeness_pct"] >= 0
    assert result["rated_hospitals"] + result["unrated_hospitals"] == result["total_hospitals"]