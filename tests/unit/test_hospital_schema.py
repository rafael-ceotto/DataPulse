import pytest

from app.schemas.hospital import Hospital

def test_hospital_valid():
    hospital = Hospital(
        facility_id="12345",
        facility_name="Test Hospital",
        address="123 Main St",
        city="Boston",
        state="MA",
        zip_code="02108",
        hospital_type="Acute Care Hospitals",
        hospital_ownership ="Voluntary non-profit",
        emergency_services="Yes",
        overall_rating="5"
    )
    
    assert hospital.facility_id == "12345"
    assert hospital.facility_name == "Test Hospital"
    assert hospital.overall_rating == 5
    
def test_overall_rating_empty():
    hospital = Hospital(
        facility_id="12345",
        facility_name="Test Hospital",
        address="123 Main St",
        city="Boston",
        state="MA",
        zip_code="02108",
        hospital_type="Acute Care Hospitals",
        hospital_ownership="Voluntary non-profit",
        emergency_services="Yes",
        overall_rating="",
    )

    assert hospital.overall_rating is None
    
def test_overall_rating_not_available():
    hospital = Hospital(
        facility_id="12345",
        facility_name="Test Hospital",
        address="123 Main St",
        city="Boston",
        state="MA",
        zip_code="02108",
        hospital_type="Acute Care Hospitals",
        hospital_ownership="Voluntary non-profit",
        emergency_services="Yes",
        overall_rating="Not Available",
    )

    assert hospital.overall_rating is None
    
def test_overall_rating_integer():
    hospital = Hospital(
        facility_id="12345",
        facility_name="Test Hospital",
        address="123 Main St",
        city="Boston",
        state="MA",
        zip_code="02108",
        hospital_type="Acute Care Hospitals",
        hospital_ownership="Voluntary non-profit",
        emergency_services="Yes",
        overall_rating="4",
    )

    assert hospital.overall_rating == 4