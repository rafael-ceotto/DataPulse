from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class HospitalInfection(Base):
    __tablename__ = "hospital_infections"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(String, ForeignKey("hospitals.facility_id"), nullable=False)
    facility_name: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    measure_id: Mapped[str] = mapped_column(String, nullable=False)
    measure_name: Mapped[str] = mapped_column(String, nullable=False)
    compared_to_national: Mapped[str | None] = mapped_column(String, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String, nullable=True)
    end_date: Mapped[str | None] = mapped_column(String, nullable=True)