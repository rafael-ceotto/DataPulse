import httpx
import json
import boto3
import os

S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

def download_and_upload():
    print("Downloading IBGE municipios...")
    r = httpx.get(
        "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
        timeout=30.0
    )
    data = r.json()
    print(f"Total: {len(data)} municipios")

    # Build lookup: 6-digit code -> city name
    lookup = {}
    for m in data:
        code_6 = str(m["id"])[:6]
        lookup[code_6] = m["nome"]

    print(f"Lookup size: {len(lookup)}")
    print(f"Sample: 120040 -> {lookup.get('120040')}")

    # Upload to S3
    s3 = get_s3_client()
    s3.put_object(
        Bucket=S3_BUCKET,
        Key="brazil/reference/ibge_municipios.json",
        Body=json.dumps(lookup, ensure_ascii=False).encode("utf-8"),
    )
    print("Uploaded to S3: brazil/reference/ibge_municipios.json")

if __name__ == "__main__":
    download_and_upload()