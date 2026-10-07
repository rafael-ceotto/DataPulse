import os
import httpx
import asyncio
import time
import asyncpg

DB_URL = os.getenv("DB_URL", "postgresql://datapulse:datapulse@db:5432/datapulse")


def nominatim_search(name: str) -> dict | None:
    time.sleep(1.1)
    variants = [
        name,
        name.replace("Hôpital", "").replace("Hospital", "").strip(),
        name.replace("Centre hospitalier", "").strip(),
        name.split("(")[0].strip(),
        name.split(",")[0].strip(),
    ]
    for variant in dict.fromkeys(variants):
        try:
            r = httpx.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{variant} Canada",
                    "format": "json",
                    "addressdetails": 1,
                    "limit": 3,
                },
                timeout=15.0,
                headers={"User-Agent": "DataPulse/1.0"},
            )
            if not r.text.strip():
                time.sleep(2)
                continue
            results = r.json()
            canada_results = [
                res for res in results
                if res.get("address", {}).get("country_code", "").lower() == "ca"
                and res.get("type") in ("hospital", "clinic", "doctors", "healthcare")
            ]
            if canada_results:
                return canada_results[0]
        except Exception as e:
            print(f"  Nominatim error for '{variant}': {e}")
        time.sleep(1.1)
    return None


def nominatim_reverse(lat: float, lon: float) -> dict | None:
    time.sleep(1.1)
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1},
            timeout=15.0,
            headers={"User-Agent": "DataPulse/1.0"},
        )
        if r.status_code == 200 and r.text.strip():
            return r.json()
    except Exception as e:
        print(f"  Reverse geocoding error: {e}")
    return None


def extract_address(address_data: dict) -> tuple:
    road = address_data.get("road") or address_data.get("pedestrian")
    house_number = address_data.get("house_number")
    postcode = address_data.get("postcode")
    city = (
        address_data.get("city")
        or address_data.get("town")
        or address_data.get("village")
        or address_data.get("suburb")
        or address_data.get("municipality")
    )
    state = (
        address_data.get("state")
        or address_data.get("province")
    )
    address_str = ", ".join(p for p in [house_number, road] if p) or None
    return address_str, postcode, city, state


async def enrich():
    conn = await asyncpg.connect(DB_URL.replace("+asyncpg", ""))
    db_hospitals = await conn.fetch(
        """SELECT facility_id, facility_name, telephone_number, address, zip_code, city, state, latitude, longitude
           FROM hospitals WHERE country = 'CA'"""
    )
    print(f"DB has {len(db_hospitals)} Canada hospitals")

    updated = 0
    for db_h in db_hospitals:
        db_name = db_h["facility_name"]
        has_address = bool(db_h["address"] and db_h["address"].strip())
        has_zip = bool(db_h["zip_code"] and db_h["zip_code"].strip())

        if has_address and has_zip:
            print(f"Skipping (already complete): {db_name}")
            continue

        print(f"\nSearching: {db_name}")

        address_data = None

        # Phase 1: search by name (Canada only, hospital type)
        result = nominatim_search(db_name)
        if result:
            print(f"  Name match: {result.get('display_name', '')[:80]}")
            address_data = result.get("address", {})

        # Phase 2: reverse geocoding fallback
        if not address_data and db_h["latitude"] and db_h["longitude"]:
            print(f"  Trying reverse geocoding ({db_h['latitude']}, {db_h['longitude']})")
            rev = nominatim_reverse(float(db_h["latitude"]), float(db_h["longitude"]))
            if rev:
                address_data = rev.get("address", {})
                print(f"  Reverse match: {rev.get('display_name', '')[:80]}")

        if not address_data:
            print(f"  No data found")
            continue

        addr, postcode, city, state = extract_address(address_data)

        update_addr = addr if not has_address else None
        update_zip = postcode if not has_zip else None
        update_city = city if not db_h["city"] else None
        update_state = state if db_h["state"] in ("Canada", "", None) else None

        if update_addr or update_zip or update_city or update_state:
            await conn.execute(
                """UPDATE hospitals SET
                    address = COALESCE($1, address),
                    zip_code = COALESCE($2, zip_code),
                    city = COALESCE($3, city),
                    state = COALESCE($4, state)
                WHERE facility_id = $5""",
                update_addr, update_zip, update_city, update_state, db_h["facility_id"]
            )
            updated += 1
            print(f"  Updated: address={update_addr}, zip={update_zip}, city={update_city}, state={update_state}")
        else:
            print(f"  Nothing new to update")

    print(f"\nTotal updated: {updated}/{len(db_hospitals)}")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(enrich())