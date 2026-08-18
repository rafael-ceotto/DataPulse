import asyncio
import csv
import io

import httpx
from pydantic import ValidationError

from backend.app.schemas.hospital import Hospital

URL = "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1785189955/Hospital_General_Information.csv"


async def fetch_data_cms() -> str | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        print(f"Couldn't retrieve data from CMS: {e}")
        return None


def parse_hospitals(csv_text: str) -> list[Hospital]:
    rows = csv.DictReader(io.StringIO(csv_text))
    hospitals = []

    for row in rows:
        try:
            hospitals.append(Hospital(
                facility_id=row["Facility ID"],
                facility_name=row["Facility Name"],
                address=row["Address"],
                city=row["City/Town"],
                state=row["State"],
                zip_code=row["ZIP Code"],
                hospital_type=row["Hospital Type"],
                hospital_ownership=row["Hospital Ownership"],
                emergency_services=row["Emergency Services"],
                overall_rating=row["Hospital overall rating"],
            ))
        except ValidationError as e:
            print(f"Validation error for hospital {row.get('Facility ID', 'unknown')}: {e}")

    return hospitals


if __name__ == "__main__":
    async def main():
        csv_text = await fetch_data_cms()
        if csv_text:
            hospitals = parse_hospitals(csv_text)
            print(f"Total hospitals parsed: {len(hospitals)}")
            print(hospitals[0])

    asyncio.run(main())