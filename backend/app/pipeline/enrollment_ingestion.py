import csv, io, httpx
from httpx import AsyncClient, HTTPError
from pydantic import ValidationError
from app.schemas.insurance import HospitalEnrollment
from app.core.config import settings

URL = "https://data.cms.gov/sites/default/files/2026-08/bcf5ccda-1482-4c43-8198-de1efa2f83c8/Hospital_Enrollments_2026.07.31.csv"

async def fetch_enrollment_cms() -> str | None:
    try:
        async with AsyncClient(timeout=60.0) as client:
            response = await client.get(settings.CMS_HOSPITAL_ENROLLMENTS_URL)
            response.raise_for_status()
            return response.text
    except HTTPError as e:
        print(f"Couldn't retrieve enrollment data from CMS: {e}")
        return None
    
def parse_enrollment(csv_text: str) -> list[HospitalEnrollment]:
    rows = csv.DictReader(io.StringIO(csv_text))
    enrollments = []
    for row in rows:
        try:
            enrollments.append(HospitalEnrollment(
                facility_id=row["CCN"],
                npi=row.get("NPI"),
                organization_name=row.get("ORGANIZATION NAME"),
                enrollment_state=row.get("ENROLLMENT STATE"),
                proprietary_nonprofit=row.get("PROPRIETARY NONPROFIT"),
                is_acute_care=row.get("SUBGROUP - ACUTE CARE", ""),
                is_psychiatric=row.get("SUBGROUP - PSYCHIATRIC", ""),
                is_rehabilitation=row.get("SUBGROUP - REHABILITATION", ""),
                is_childrens=row.get("SUBGROUP - CHILDRENS", ""),
                is_long_term=row.get("SUBGROUP - LONG-TERM", ""),
                is_swing_bed=row.get("SUBGROUP - SWING-BED APPROVED", ""),
            ))
        except ValidationError as e:
            print(f"Validation error for CCN {row.get('CCN', 'unknown')}: {e}")
    return enrollments