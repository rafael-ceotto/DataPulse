import os
import boto3
import tempfile
import httpx
import csv
import io
import pandas as pd

S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

FINESS_URL = "https://static.data.gouv.fr/resources/finess-extraction-du-fichier-des-etablissements/20260512-091308/etalab-cs1100502-stock-20260512-0339.csv"
GEOCODE_URL = "https://api-adresse.data.gouv.fr/search/csv/"

HOSPITAL_TYPES = {
    "355": "Centre Hospitalier",
    "101": "Centre Hospitalier Régional",
    "106": "Centre Hospitalier Local",
    "292": "Centre Hospitalier Spécialisé",
}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def download_finess() -> list[dict]:
    """Download FINESS CSV and filter hospital types."""
    print("Downloading FINESS data...")
    r = httpx.get(FINESS_URL, timeout=60.0, follow_redirects=True)
    r.raise_for_status()

    lines = r.text.split('\n')
    reader = csv.reader(io.StringIO('\n'.join(lines[1:])), delimiter=';')

    hospitals = []
    skipped = 0
    for row in reader:
        if len(row) < 32:
            skipped += 1
            continue
        code_type = row[18]
        if code_type not in HOSPITAL_TYPES:
            continue

        try:
            cp_ville = row[15].strip()
            parts = cp_ville.split(' ', 1)
            postcode = parts[0] if parts else ""
            ville = parts[1] if len(parts) > 1 else ""

            numero = row[7].strip()
            type_voie = row[8].strip()
            voie = row[9].strip()
            address = f"{numero} {type_voie} {voie}".strip()

            hospitals.append({
                "facility_id": row[1].strip(),
                "facility_name": row[4].strip() or row[3].strip(),
                "address": address,
                "city": ville,
                "postcode": postcode,
                "cp_ville": cp_ville,
                "department": row[14].strip(),
                "telephone": row[16].strip(),
                "hospital_type_code": code_type,
                "hospital_type": HOSPITAL_TYPES.get(code_type, row[19].strip()),
                "ownership": row[27].strip(),
            })
        except IndexError as e:
            print(f"IndexError on row with {len(row)} fields: {row[:5]} — {e}")
            continue

    print(f"Skipped rows (< 32 fields): {skipped}")
    print(f"Hospitals found: {len(hospitals)}")
    return hospitals


def bulk_geocode(hospitals: list[dict]) -> dict:
    """Geocode using api-adresse.data.gouv.fr bulk CSV endpoint."""
    print(f"Geocoding {len(hospitals)} hospitals...")

    csv_content = "adresse\n" + "\n".join(h["cp_ville"] for h in hospitals)
    geocodes = {}

    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            GEOCODE_URL,
            files={"data": ("addresses.csv", csv_content, "text/csv")},
        )
        if r.status_code == 200:
            reader = csv.DictReader(io.StringIO(r.text))
            for row in reader:
                addr = row.get("adresse", "")
                lat = row.get("latitude")
                lng = row.get("longitude")
                city = row.get("result_city", "")
                region = row.get("result_context", "")
                if lat and lng:
                    geocodes[addr] = {
                        "latitude": float(lat),
                        "longitude": float(lng),
                        "city": city,
                        "region": region.split(",")[-1].strip() if region else "",
                    }

    print(f"Geocoded: {len(geocodes)}")
    return geocodes


def process_and_upload(hospitals: list[dict], geocodes: dict) -> None:
    """Build DataFrame and upload as CSV to S3."""
    rows = []
    for h in hospitals:
        geo = geocodes.get(h["cp_ville"], {})
        rows.append({
            "facility_id": h["facility_id"],
            "facility_name": h["facility_name"],
            "address": h["address"],
            "city": geo.get("city") or h["city"],
            "state": geo.get("region") or h["department"],
            "zip_code": h["postcode"],
            "hospital_type": h["hospital_type"],
            "hospital_ownership": h["ownership"],
            "emergency_services": "",
            "overall_rating": None,
            "telephone_number": h["telephone"] or None,
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
            "country": "FR",
            "normalized_score": None,
            "rating_system": "HAS Certification",
            "raw_rating_label": None,
        })

    df = pd.DataFrame(rows)
    print(f"Total hospitals: {len(df)}")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    tmp.close()

    s3 = get_s3_client()
    s3_key = "hospitals/processed/country=FR/finess_hospitals.csv"
    with open(tmp.name, "rb") as f:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
    print(f"Uploaded to S3: {s3_key}")
    os.unlink(tmp.name)


if __name__ == "__main__":
    hospitals = download_finess()
    geocodes = bulk_geocode(hospitals)
    process_and_upload(hospitals, geocodes)