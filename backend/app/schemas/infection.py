from pydantic import BaseModel, field_validator

class HospitalInfection(BaseModel):
    facility_id: str
    facility_name: str
    state: str
    measure_id: str
    measure_name: str
    compared_to_national: str | None = None
    score: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    
@field_validator("score", mode="before")
@classmethod
def empty_to_none(cls, v):
    if v in ("", "N/A", "Not available", "Not Available"):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        print(f"=== SCORE PARSE ERROR: repr={repr(v)} ===")
        return None