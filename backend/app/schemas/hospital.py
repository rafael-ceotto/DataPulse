from pydantic import BaseModel, field_validator


class Hospital(BaseModel):
    facility_id: str
    facility_name: str
    address: str
    city: str
    state: str
    zip_code: str
    hospital_type: str
    hospital_ownership: str
    emergency_services: str
    overall_rating: int | None = None
    telephone_number: str | None = None

    @field_validator("overall_rating", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v in ("", "N/A", "Not available", "Not Available"):
            return None
        return v


if __name__ == "__main__":
    hospital = Hospital(
        facility_id="010001",
        facility_name="SOUTHEAST HEALTH MEDICAL CENTER",
        address="1108 ROSS CLARK CIRCLE",
        city="DOTHAN",
        state="AL",
        zip_code="36301",
        hospital_type="Acute Care Hospitals",
        hospital_ownership="Government - Hospital District or Authority",
        emergency_services="Yes",
        overall_rating=""
    )
    print(hospital)