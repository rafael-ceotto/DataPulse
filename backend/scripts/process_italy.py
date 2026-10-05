import os
import boto3
import tempfile
import httpx
import pandas as pd

S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

QUERY = """
SELECT ?hospital ?name ?cityLabel ?lat ?lng ?address ?phone WHERE {
  ?hospital wdt:P31 wd:Q16917.
  ?hospital wdt:P17 wd:Q38.
  ?hospital wdt:P625 ?coords.
  BIND(geof:latitude(?coords) AS ?lat)
  BIND(geof:longitude(?coords) AS ?lng)
  OPTIONAL { ?hospital wdt:P131 ?city. }
  OPTIONAL { ?hospital wdt:P969 ?address. }
  OPTIONAL { ?hospital wdt:P1329 ?phone. }
  OPTIONAL { ?hospital rdfs:label ?name. FILTER(LANG(?name) = "it") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}
"""


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def fetch_hospitals() -> list[dict]:
    print("Fetching Italian hospitals from Wikidata...")
    r = httpx.get(
        WIKIDATA_SPARQL,
        params={"query": QUERY, "format": "json"},
        timeout=60.0,
        headers={"User-Agent": "DataPulse/1.0"},
    )
    r.raise_for_status()
    results = r.json().get("results", {}).get("bindings", [])
    print(f"Found: {len(results)} hospitals")
    return results


def process_and_upload(results: list[dict]) -> None:
    rows = []
    seen = set()
    for item in results:
        hospital_id = item.get("hospital", {}).get("value", "").split("/")[-1]
        if hospital_id in seen:
            continue
        seen.add(hospital_id)

        name = item.get("name", {}).get("value", "") or item.get("hospitalLabel", {}).get("value", "")
        city = item.get("cityLabel", {}).get("value", "")
        lat = item.get("lat", {}).get("value")
        lng = item.get("lng", {}).get("value")
        address = item.get("address", {}).get("value", "")
        phone = item.get("phone", {}).get("value")

        rows.append({
            "facility_id": hospital_id,
            "facility_name": name,
            "address": address,
            "city": city,
            "state": "",
            "zip_code": "",
            "hospital_type": "Ospedale",
            "hospital_ownership": "",
            "emergency_services": "",
            "overall_rating": None,
            "telephone_number": phone,
            "latitude": float(lat) if lat else None,
            "longitude": float(lng) if lng else None,
            "country": "IT",
            "normalized_score": None,
            "rating_system": "SSN — structural data only",
            "raw_rating_label": None,
        })

    df = pd.DataFrame(rows)
    print(f"Total unique hospitals: {len(df)}")
    print(df[['facility_id', 'facility_name', 'city', 'latitude']].head(5).to_string())

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    tmp.close()

    s3 = get_s3_client()
    s3_key = "hospitals/processed/country=IT/italy_hospitals.csv"
    with open(tmp.name, "rb") as f:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
    print(f"Uploaded to S3: {s3_key}")
    os.unlink(tmp.name)


if __name__ == "__main__":
    results = fetch_hospitals()
    process_and_upload(results)