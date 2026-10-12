from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class HospitalEnrollment(Base):
    __tablename__ = "hospital_enrollments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(String, ForeignKey("hospitals.facility_id"), nullable=False, unique=True)
    npi: Mapped[str | None] = mapped_column(String, nullable=True)
    organization_name: Mapped[str | None] = mapped_column(String, nullable=True)
    enrollment_state: Mapped[str | None] = mapped_column(String, nullable=True)
    proprietary_nonprofit: Mapped[str | None] = mapped_column(String, nullable=True)
    is_acute_care: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_psychiatric: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_rehabilitation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_childrens: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_long_term: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_swing_bed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)