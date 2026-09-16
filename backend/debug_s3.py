from app.core.s3 import get_s3_client, BUCKET_NAME

client = get_s3_client()
response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='pipeline-runs/')
objects = response.get('Contents', [])

for obj in objects:
    key = obj['Key']
    parts = key.split('/')
    print(f'Key: {key}')
    print(f'Parts: {parts}')
    print(f'Length: {len(parts)}')
    print(f'Ends with json: {key.endswith("hospitals.json")}')
    print()
