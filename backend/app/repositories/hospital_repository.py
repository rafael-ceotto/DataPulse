from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.hospital import Hospital as HospitalModel

from app.schemas.hospital import Hospital as HospitalSchema


async def save_hospitals(session: AsyncSession, 
                        hospitals: list[HospitalSchema],
                        ) -> None: 
                            try:
                                for hospital in hospitals:
                                    db_hospital = HospitalModel(
                                        facility_id=hospital.facility_id,
                                        facility_name=hospital.facility_name,
                                        address=hospital.address,
                                        city=hospital.city,
                                        state=hospital.state,
                                        zip_code=hospital.zip_code,
                                        hospital_type=hospital.hospital_type,
                                        hospital_ownership=hospital.hospital_ownership,
                                        emergency_services=hospital.emergency_services,
                                        overall_rating=hospital.overall_rating,
                                    )
                                    session.add(db_hospital)
                                await session.commit()
                            except SQLAlchemyError as e:
                                await session.rollback()
                                raise e