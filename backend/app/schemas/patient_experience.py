from pydantic import BaseModel, ConfigDict

class HospitalPatientExperience(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hcahps_measure_id: str
    hcahps_question: str | None = None
    patient_experience_category: str | None = None
    star_rating: str | None = None
    answer_percent: str | None = None
    linear_mean_value: str | None = None
    number_of_completed_surveys: str | None = None
    survey_response_rate_percent: str | None = None
    start_date: str | None = None
    end_date: str | None = None