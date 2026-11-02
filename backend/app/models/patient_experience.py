from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint

from app.core.database import Base


class HospitalPatientExperience(Base):
    __tablename__ = "hospital_patient_experience"

    id = Column(Integer, primary_key=True)
    facility_id = Column(String, nullable=False, index=True)
    hcahps_measure_id = Column(String, nullable=False)
    hcahps_question = Column(String, nullable=True)
    hcahps_answer_description = Column(String, nullable=True)
    patient_experience_category = Column(String, nullable=True, index=True)
    is_star_rating = Column(Boolean, nullable=False, default=False, index=True)
    star_rating = Column(String, nullable=True)
    answer_percent = Column(String, nullable=True)
    linear_mean_value = Column(String, nullable=True)
    number_of_completed_surveys = Column(String, nullable=True)
    survey_response_rate_percent = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "facility_id", "hcahps_measure_id", name="uq_patient_experience_facility_measure"
        ),
    )