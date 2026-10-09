import asyncio
import asyncpg
import json
import os
import re
from pathlib import Path

DB_URL = os.environ.get("DATABASE_URL", "postgresql://datapulse:datapulse@localhost:5433/datapulse")

# Map country code -> GeoJSON file path
DATA_DIR = Path(__file__).parent.parent.parent / "data"

COUNTRY_FILES = {
    "CA": DATA_DIR / "osm_CA.json",
    "ES": DATA_DIR / "osm_ES.json",
    "IT": DATA_DIR / "osm_IT.json",
    "PT": DATA_DIR / "osm_PT.json",
    "BE": DATA_DIR / "osm_BE.json",
}


def clean_phone(phone: str) -> str:
    if not phone:
        return ""
    phone = phone.strip().replace("\x00", "")
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 6:
        return ""
    return phone


def load_phone_map(geojson_path: Path) -> dict:
    """Read GeoJSON exported from Overpass Turbo and return {name_lower: phone}."""
    with open(geojson_path, encoding="utf-8") as f:
        data = json.load(f)

    phone_map = {}

    # Overpass Turbo GeoJSON export wraps elements as features
    features = data.get("features", [])

    # Also handle raw Overpass JSON (elements array) in case file is that format
    elements = data.get("elements", [])

    entries = []
    if features:
        entries = [f.get("properties", {}) for f in features]
    elif elements:
        entries = [el.get("tags", {}) for el in elements]

    for tags in entries:
        if not tags:
            continue
        name = tags.get("name", "").strip().lower()
        phone = clean_phone(tags.get("contact:phone", "") or tags.get("phone", ""))
        if name and phone:
            phone_map[name] = phone

    return phone_map


def name_match(db_name: str, osm_name: str) -> bool:
    a = db_name.lower().strip()
    b = osm_name.lower().strip()
    return a == b or a in b or b in a


async def main():
    conn = await asyncpg.connect(DB_URL)

    for country_code, geojson_path in COUNTRY_FILES.items():
        if not geojson_path.exists():
            print(f"{country_code}: file not found at {geojson_path}, skipping.")
            continue

        rows = await conn.fetch(
            """
            SELECT facility_id, facility_name FROM hospitals
            WHERE country = $1
            AND (telephone_number IS NULL OR telephone_number = '')
            """,
            country_code,
        )

        if not rows:
            print(f"{country_code}: no hospitals without phone, skipping.")
            continue

        print(f"\n{country_code}: {len(rows)} hospitals without phone")

        phone_map = load_phone_map(geojson_path)
        print(f"  OSM file has {len(phone_map)} entries with phone")

        updated = 0
        not_found = []

        for row in rows:
            facility_id = row["facility_id"]
            facility_name = row["facility_name"]
            name_lower = facility_name.lower().strip()
            phone = None

            if name_lower in phone_map:
                phone = phone_map[name_lower]
            else:
                for osm_name, osm_phone in phone_map.items():
                    if name_match(name_lower, osm_name):
                        phone = osm_phone
                        break

            if phone:
                await conn.execute(
                    "UPDATE hospitals SET telephone_number = $1 WHERE facility_id = $2",
                    phone,
                    facility_id,
                )
                updated += 1
            else:
                not_found.append(facility_name)

        print(f"  Updated {updated}/{len(rows)} hospitals")
        if not_found:
            print(
                f"  No match ({len(not_found)}): {not_found[:5]}{'...' if len(not_found) > 5 else ''}"
            )

    await conn.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())