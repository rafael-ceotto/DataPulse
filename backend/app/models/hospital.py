from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    facility_id: Mapped[str] = mapped_column(String, primary_key=True)
    facility_name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    zip_code: Mapped[str] = mapped_column(String, nullable=False)
    hospital_type: Mapped[str] = mapped_column(String, nullable=False)
    hospital_ownership: Mapped[str] = mapped_column(String, nullable=False)
    emergency_services: Mapped[str] = mapped_column(String, nullable=False)
    overall_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)