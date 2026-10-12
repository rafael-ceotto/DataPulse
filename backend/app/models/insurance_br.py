from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class HospitalInsuranceNetwork(Base):
    __tablename__ = "hospital_insurance_network"
    __table_args__ = (
        UniqueConstraint("facility_id", "operator_code", name="uq_hospital_operator"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(String, ForeignKey("hospitals.facility_id"), nullable=False)
    operator_code: Mapped[str] = mapped_column(String, nullable=False)
    operator_name: Mapped[str | None] = mapped_column(String, nullable=True)
    has_emergency_coverage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    coverage_type: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_relationship: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)