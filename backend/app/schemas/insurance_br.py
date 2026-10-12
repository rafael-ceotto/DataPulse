from pydantic import BaseModel, field_validator

class HospitalInsuranceNetworkEntry(BaseModel):
    facility_id: str
    operator_code: str
    operator_name: str | None = None
    has_emergency_coverage: bool = False
    coverage_type: str | None = None
    provider_relationship: str | None = None
    is_active: bool = True
    
    @field_validator("has_emergency_coverage", mode="before")
    @classmethod
    def one_to_bool(cls, v):
        return str(v).strip() == "1"
    
    @field_validator("operator_name", "coverage_type", "provider_relationship", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v in ("", "Não informado", "Nao informado", None):
            return None
        return v