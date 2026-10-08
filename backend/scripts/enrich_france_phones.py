import asyncio
import asyncpg
import httpx
import os

DB_URL = os.environ.get("DATABASE_URL", "postgresql://datapulse:datapulse@db:5432/datapulse")

FINESS_URL = "https://www.data.gouv.fr/api/1/datasets/r/98f3161f-79ff-4f16-8f6a-6d571a80fea2"

async def main():
    print("Downloading FINESS CSV...")
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        r = await client.get(FINESS_URL)
        r.raise_for_status()
        content = r.text

    print(f"Downloaded {len(content)} bytes. Parsing...")

    # CSV is semicolon-delimited, no proper header, positional columns
    # Row format: structureet;finess_et;finess_ej;nom_court;nom_long;...;telephone;fax;...
    # telephone is at index 16
    phone_map = {}
    for line in content.splitlines():
        if not line.startswith("structureet"):
            continue
        parts = line.split(";")
        if len(parts) < 17:
            continue
        finess_et = parts[1].strip()   # établissement
        finess_ej = parts[2].strip()   # entité juridique
        phone = parts[16].strip()
        if phone:
            if finess_et:
                phone_map[finess_et] = phone
            if finess_ej and finess_ej not in phone_map:
                phone_map[finess_ej] = phone

    print(f"Found {len(phone_map)} FINESS entries with phone numbers")    
    conn = await asyncpg.connect(DB_URL)

    # Get French hospitals without phone
    rows_db = await conn.fetch("""
        SELECT facility_id FROM hospitals
        WHERE country = 'FR' AND (telephone_number IS NULL OR telephone_number = '')
    """)
    print(f"French hospitals without phone: {len(rows_db)}")

    updated = 0
    not_found = []
    for row in rows_db:
        facility_id = row["facility_id"]  # e.g. "FR-0750100814"
        finess_num = facility_id.replace("FR-", "").strip()

        phone = phone_map.get(finess_num)
        if phone:
            await conn.execute(
                "UPDATE hospitals SET telephone_number = $1 WHERE facility_id = $2",
                phone, facility_id
            )
            updated += 1
        else:
            not_found.append(finess_num)

    await conn.close()

    print(f"Updated {updated}/{len(rows_db)} French hospitals with phone numbers")
    if not_found:
        print(f"Not found in FINESS ({len(not_found)}): {not_found[:10]}{'...' if len(not_found) > 10 else ''}")

if __name__ == "__main__":
    asyncio.run(main())