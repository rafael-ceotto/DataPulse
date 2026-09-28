import os, boto3, tempfile, httpx, json, time
import pandas as pd

S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

NHS_ODS_BASE = "https://directory.spineservices.nhs.uk/ORD/2-0-0"
POSTCODES_API = "https://api.postcodes.io/postcodes"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    
def fetch_nhs_trusts() -> list[dict]:
    """Retrieving all active NHS Trusts from ODS."""
    print("Fetching NHS Trusts from ODS...")
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{NHS_ODS_BASE}/organisations?PrimaryRoleId=RO197&Limit=1000")
        r.raise_for_status()
        orgs = r.json().get("Organisations", [])
        active = [o for o in orgs if o.get("Status") == "Active"]
        print(f"Found {len(active)} active NHS Trusts")
        return active
    
def fetch_org_details(org_id: str, client: httpx.Client) -> dict:
    """Fetch full details for an org"""
    try:
       r = client.get(f"{NHS_ODS_BASE}/organisations/{org_id}", timeout=10.0)
       if r.status_code == 200:
           return r.json().get("Organisation", {})
    except Exception as e:
        print(f" Error fetching {org_id}: {e}")
    return {}

def bulk_geocode_postcodes(postcodes: list[str]) -> dict:
    """Geocode postcodes in bulk using postcodes.io."""
    result = {}
    batch_size = 100
    with httpx.Client(timeout=15.0) as client:
        for i in range(0, len(postcodes), batch_size):
            batch = postcodes[i:i + batch_size]
            try:
                r = client.post(POSTCODES_API, json={"postcodes": batch})
                if r.status_code == 200:
                    for item in r.json().get("result", []):
                        res =  item.get("result")
                        if res:
                            result[item["query"]] = {
                                "latitude": res.get("latitude"),
                                "longitude": res.get("longitude"),
                                "city": res.get("admin_district") or res.get("region"),
                                "region": res.get("region"),
                            }
            except Exception as e:
                print(f" Geocoding error: {e}")
            time.sleep(0.2)
    print(f"Geocoded {len(result)} postcodes")
    return result

def process_and_upload(trusts: list[dict], details: dict, geocodes: dict) -> None:
    """Build DF -> Parquet -> S3"""
    rows = []
    for trust in trusts:
        org_id = trust["OrgId"]
        detail = details.get(org_id, {})
        postcode = trust.get("PostCode", "")
        geo = geocodes.get(postcode, {})
        
        geo_loc = detail.get("GeoLoc", {}).get("Location", {})
        addr_parts = [
            geo_loc.get("AddrLn1", ""),
            geo_loc.get("AddrLn2", ""),
            geo_loc.get("AddrLn3", ""),
        ]
        address = " ".join(p for p in addr_parts if p).strip()
        
        rows.append({
            "facility_id": org_id,
            "facility_name": trust["Name"],
            "address": address,
            "city": geo.get("city") or geo_loc.get("Town", ""),
            "state": geo.get("region", "England"),
            "zip_code": postcode,
            "hospital_type": "NHS Trust",
            "hospital_ownership": "NHS",
            "emergency_services": "",
            "overall_rating": None,
            "telephone_number": None,
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
            "country": "GB",
            "normalized_score": None,
            "rating_system": "CQC (Care Quality Commission)",
            "raw_rating_label": None,
        })
        
    df = pd.DataFrame(rows)
    print(f"Total hospitals: {len(df)}")
    
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    tmp.close()
    
    s3 = get_s3_client()
    s3_key = "hospitals/processed/country=GB/nhs_trusts.csv"
    with open(tmp.name, "rb") as f:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
    print(f"Uploaded to S3: {s3_key}")
    os.unlink(tmp.name)
    
if __name__ == "__main__":
    trusts = fetch_nhs_trusts()
    print("Fetching each trust details...")
    details = {}
    with httpx.Client(timeout=10.0) as client:
        for i, trust in enumerate(trusts):
            org_id = trust["OrgId"]
            details[org_id] = fetch_org_details(org_id, client)
            if (i+1) % 50 == 0:
                print(f" {i+1}/{len(trusts)} done")
            time.sleep(0.1)
    print(f"Details fetched: {len(details)}")
    postcodes = [t.get("PostCode", "") for t in trusts if t.get("PostCode")]
    geocodes = bulk_geocode_postcodes(postcodes)
    process_and_upload(trusts, details, geocodes)