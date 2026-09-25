import boto3
import tempfile
import os
import duckdb

client = boto3.client(
    's3',
    endpoint_url='http://floci:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

response = client.list_objects_v2(Bucket='datapulse', Prefix='hospitals/processed/country=BR/state=AC/')
objects = response.get('Contents', [])
print(f"Files in S3 for AC: {len(objects)}")
for obj in objects:
    print(f"  {obj['Key']} - {obj['LastModified']}")

if objects:
    key = objects[0]['Key']
    body = client.get_object(Bucket='datapulse', Key=key)['Body'].read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.parquet')
    tmp.write(body)
    tmp.close()
    
    con = duckdb.connect()
    df = con.execute(f"SELECT facility_id, facility_name, address FROM read_parquet('{tmp.name}') LIMIT 5").fetchdf()
    print(df.to_string())
    os.unlink(tmp.name)