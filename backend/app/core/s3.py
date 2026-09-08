import boto3
import os
from botocore.config import Config

FLOCI_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION",  "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "datapulse")

_s3_client = None

def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url = FLOCI_ENDPOINT,
            region_name = AWS_REGION,
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            config = Config(signature_version="s3v4")
        )
    return _s3_client

async def upload_json(key: str, data: str) -> bool:
    try:
        client = get_s3_client()
        client.put_object(
            Bucket = BUCKET_NAME,
            Key=key,
            Body=data.encode("utf-8"),
            ContentType="application/json",
        )
        print(f"S3: uploaded {key}")
        return True
    except Exception as e:
        print(f"S3: upload failed for {key} - {e}")
        return False
    
async def upload_file(key:str, file_path:str) -> bool:
    try:
        client = get_s3_client()
        client.upload_file(file_path, BUCKET_NAME, key)
        print(f"S3: uploaded file {key}")
        return True
    except Exception as e:
        print(f"S3: upload failed for {key} — {e}")
        return False
    
async def download_file(key:str, destination_path: str) -> bool:
    try:
        client = get_s3_client()
        client.download_file(BUCKET_NAME, key, destination_path)
        print(f"S3: downloaded {key} to {destination_path}")
        return True
    except Exception as e:
        print(f"S3: upload failed for {key} — {e}")
        return False
    
async def list_objects(prefix: str) -> list[str]:
    try:
        client = get_s3_client()
        response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    except Exception as e:
        print(f"S3: list failed for prefix {prefix} — {e}")
        return []