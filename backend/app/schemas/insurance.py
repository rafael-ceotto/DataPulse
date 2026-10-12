from pydantic import BaseModel, field_validator

class HospitalEnrollment(BaseModel):
    facility_id: str
    npi: str | None = None
    organization_name: str | None = None
    enrollment_state: str | None = None
    proprietary_nonprofit: str | None = None
    is_acute_care: bool = False
    is_psychiatric: bool = False
    is_rehabilitation: bool = False
    is_childrens: bool = False
    is_long_term: bool = False
    is_swing_bed: bool = False

    @field_validator(
        "is_acute_care",
        "is_psychiatric",
        "is_rehabilitation",
        "is_childrens",
        "is_long_term",
        "is_swing_bed",
        mode="before",
    )
    @classmethod
    def y_to_bools(cls, v):
        return str(v).strip().upper() == "Y"
    
    @field_validator("npi", "organization_name", "enrollment_state", "proprietary_nonprofit", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v in ("", "N/A", None):
            return None
        return v