from app.pipeline.cms_ingestion import parse_hospitals

VALID_CSV = """Facility ID,Facility Name,Address,City/Town,State,ZIP Code,County/Parish,Telephone Number,Hospital Type,Hospital Ownership,Emergency Services,Meets criteria for birthing friendly designation,Hospital overall rating,...
010001,Test Hospital,123 Main St,Boston,MA,02108,Suffolk,555-1234,Acute Care Hospitals,Voluntary non-profit - Private,Yes,,4,..."""

def test_parse_hospitals_valid_csv():
    hospitals = parse_hospitals(VALID_CSV)
    assert len(hospitals) == 1
    assert hospitals[0].facility_id == "010001"
    assert hospitals[0].facility_name == "Test Hospital"
    assert hospitals[0].overall_rating == 4
    
def test_parse_hospitals_invalid_row():
    csv_text = VALID_CSV + ("INVALID,Invalid Hospital,,,,,,,,,,,\n")
    hospitals = parse_hospitals(csv_text)
    assert len(hospitals) == 1
    assert hospitals[0].facility_id == "010001"
    
def test_parse_hospitals_empty_csv():
    hospitals = parse_hospitals("")
    assert hospitals == []    