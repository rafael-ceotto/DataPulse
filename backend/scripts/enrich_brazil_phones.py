import asyncio
import asyncpg
import os
import sys
import zipfile
import csv
import io

DB_URL = os.environ.get("DATABASE_URL", "postgresql://datapulse:datapulse@db:5432/datapulse")
ZIP_PATH = os.environ.get("CNES_ZIP_PATH", "/data/BASE_DE_DADOS_CNES_202409.ZIP")

# Estabilishment main file
ESTAB_CSV = "tbEstabelecimento202409.csv"


async def main():
    if not os.path.exists(ZIP_PATH):
        print(f"ERROR: ZIP not found at {ZIP_PATH}")
        return

    file_size = os.path.getsize(ZIP_PATH) / 1024 / 1024
    print(f"Found ZIP: {ZIP_PATH} ({file_size:.0f} MB)")

    print(f"Reading {ESTAB_CSV} from ZIP...")
    with zipfile.ZipFile(ZIP_PATH) as z:
        with z.open(ESTAB_CSV) as f:
            # Peek at first line to detect delimiter and columns
            raw = io.TextIOWrapper(f, encoding="latin-1")
            reader = csv.DictReader(raw, delimiter=";")
            
            # Show columns
            first = next(reader, None)
            if not first:
                print("ERROR: CSV is empty!")
                return
            print(f"CSV columns: {list(first.keys())[:15]}...")  # show first 15

    # Re-read to build phone map
    phone_map = {}
    with zipfile.ZipFile(ZIP_PATH) as z:
        with z.open(ESTAB_CSV) as f:
            raw = io.TextIOWrapper(f, encoding="latin-1")
            reader = csv.DictReader(raw, delimiter=";")

            for row in reader:
                # CNES ID — CO_CNES column
                cnes_id = row.get("CO_CNES", "").strip().zfill(7)
                if not cnes_id or cnes_id == "0000000":
                    continue

                # Telefone — try NU_TELEFONE, else NU_FAX
                phone = row.get("NU_TELEFONE", "").strip()
                if not phone:
                    phone = row.get("NU_FAX", "").strip()

                # data cleansing
                phone = phone.replace("\x00", "").strip()
                if phone and phone.replace("0", "").strip():
                    phone_map[cnes_id] = phone

    print(f"Found {len(phone_map)} CNES entries with phone numbers")

    conn = await asyncpg.connect(DB_URL)

    total_br = await conn.fetchval("SELECT COUNT(*) FROM hospitals WHERE country = 'BR'")
    print(f"Total Brazilian hospitals in DB: {total_br}")

    rows_db = await conn.fetch("""
        SELECT facility_id FROM hospitals
        WHERE country = 'BR' AND (telephone_number IS NULL OR telephone_number = '')
    """)
    print(f"Brazilian hospitals without phone: {len(rows_db)}")

    updated = 0
    not_found = []

    for row in rows_db:
        facility_id = row["facility_id"]
        cnes_num = facility_id.replace("BR-", "").strip().zfill(7)
        phone = phone_map.get(cnes_num)
        if phone:
            await conn.execute(
                "UPDATE hospitals SET telephone_number = $1 WHERE facility_id = $2",
                phone, facility_id
            )
            updated += 1
        else:
            not_found.append(cnes_num)

    await conn.close()
    print(f"\nUpdated {updated}/{len(rows_db)} Brazilian hospitals with phone numbers")
    if not_found:
        print(f"Not found in CNES ({len(not_found)}): {not_found[:10]}{'...' if len(not_found) > 10 else ''}")


if __name__ == "__main__":
    asyncio.run(main())
