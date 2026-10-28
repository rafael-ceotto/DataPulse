from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.core.database import Base

class HospitalProcedureOutcome(Base):
    __tablename__ = "hospital_procedure_outcomes"
    
    id = Column(Integer, primary_key=True)
    facility_id = Column(String, nullable=False, index=True)
    measure_id = Column(String, nullable=False)       
    measure_name = Column(String, nullable=False)     
    procedure_category = Column(String, nullable=True, index=True)
    compared_to_national = Column(String, nullable=True)  
    denominator = Column(String, nullable=True)   
    score = Column(String, nullable=True)
    lower_estimate = Column(String, nullable=True)
    higher_estimate = Column(String, nullable=True)
    number_of_patients = Column(String, nullable=True)
    number_of_patients_returned = Column(String, nullable=True)
    footnote = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("facility_id", "measure_id", name="uq_procedure_outcome_facility_measure"),)