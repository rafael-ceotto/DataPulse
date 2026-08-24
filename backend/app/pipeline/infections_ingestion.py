import csv
import io
import httpx

from pydantic import ValidationError

from app.schemas.infection import HospitalInfection

URL = "https://data.cms.gov/provider-data/sites/default/files/resources/43825e12dc0c923df9ba5cbdf473c9d5_1785189952/Healthcare_Associated_Infections-Hospital.csv"

async def fetch_infections_cms() -> str | None:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(URL)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        print(f"Couldn't retrieve infection data from CMS: {e}")
        return None
    
def parse_infections(csv_text: str) -> list[HospitalInfection]:
    rows = csv.DictReader(io.StringIO(csv_text))
    infections = []
    
    for row in rows:
        try:
           infections.append(HospitalInfection(
                facility_id=row["Facility ID"],
                facility_name=row["Facility Name"],
                state=row["State"],
                measure_id=row["Measure ID"],
                measure_name=row["Measure Name"],
                compared_to_national=row["Compared to National"],
                score=row["Score"],
                start_date=row["Start Date"],
                end_date=row["End Date"],
            ))
        except ValidationError as e:
            print(f"Validation error for facility {row.get('Facility ID', 'unknown')}: {e}")

    return infections 