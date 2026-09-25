from sqlalchemy import Integer, String, Float
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
    telephone_number: Mapped[str | None] =  mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    country: Mapped[str | None] =  mapped_column(String(2), nullable=True, server_default="US")
    normalized_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_system: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_rating_label: Mapped[str | None] = mapped_column(String(100), nullable=True)