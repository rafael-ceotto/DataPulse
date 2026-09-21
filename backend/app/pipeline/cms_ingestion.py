import asyncio
import csv
import io

import httpx
from pydantic import ValidationError

from app.schemas.hospital import Hospital
from app.core.logging import logger

URL = "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1785189955/Hospital_General_Information.csv"
ZIP_LAT_LNG_URL = "https://gist.github.com/abatko/94d1fa8e76a3b7ce98ff8e6178c97861/raw"

_zip_lookup: dict[str, tuple[float, float]] | None = None


def get_zip_lookup() -> dict[str, tuple[float, float]]:
    global _zip_lookup
    if _zip_lookup is not None:
        return _zip_lookup

    try:
        r = httpx.get(ZIP_LAT_LNG_URL, timeout=30.0, follow_redirects=True)
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text), delimiter="\t")
        _zip_lookup = {}
        for row in reader:
            zip_code = row["ZIP"].strip().zfill(5)
            try:
                _zip_lookup[zip_code] = (float(row["LAT"]), float(row["LNG"]))
            except (ValueError, KeyError):
                continue
        logger.info("zip_lookup_loaded", count=len(_zip_lookup))
    except Exception as e:
        logger.error("zip_lookup_failed", error=str(e))
        _zip_lookup = {}

    return _zip_lookup


async def fetch_data_cms() -> str | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error("cms_fetch_failed", error=str(e))
        return None


def parse_hospitals(csv_text: str) -> list[Hospital]:
    rows = csv.DictReader(io.StringIO(csv_text))
    zip_lookup = get_zip_lookup()
    hospitals = []
    geocoded = 0

    for row in rows:
        try:
            zip_code = row["ZIP Code"].strip().zfill(5)
            coords = zip_lookup.get(zip_code)
            lat, lng = coords if coords else (None, None)
            if coords:
                geocoded += 1

            hospitals.append(Hospital(
                facility_id=row["Facility ID"],
                facility_name=row["Facility Name"],
                address=row["Address"],
                city=row["City/Town"],
                state=row["State"],
                zip_code=zip_code,
                hospital_type=row["Hospital Type"],
                hospital_ownership=row["Hospital Ownership"],
                emergency_services=row["Emergency Services"],
                overall_rating=row["Hospital overall rating"],
                telephone_number=row["Telephone Number"],
                latitude=lat,
                longitude=lng,
            ))
        except ValidationError as e:
            logger.error("hospital_validation_error", facility_id=row.get("Facility ID", "unknown"), error=str(e))

    logger.info("hospitals_parsed", total=len(hospitals), geocoded=geocoded)
    return hospitals


if __name__ == "__main__":
    async def main():
        csv_text = await fetch_data_cms()
        if csv_text:
            hospitals = parse_hospitals(csv_text)
            logger.info("parse_complete", total=len(hospitals))
            logger.info("sample", hospital=str(hospitals[0]))

    asyncio.run(main())