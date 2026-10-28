from pydantic import BaseModel, ConfigDict

class HospitalProcedureOutcome(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    measure_id: str
    measure_name: str
    procedure_category: str | None = None
    compared_to_national: str | None = None
    denominator: str | None = None
    score: str | None = None
    lower_estimate: str | None = None
    higher_estimate: str | None = None
    number_of_patients: str | None = None
    number_of_patients_returned: str | None = None
    footnote: str | None = None
    start_date: str | None = None
    end_date: str | None = None