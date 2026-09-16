from app.core.s3 import get_s3_client, BUCKET_NAME
import json

client = get_s3_client()
key = 'pipeline-runs/63ec75fb-0619-493d-9eb3-617551347529/hospitals.json'
try:
    body = client.get_object(Bucket=BUCKET_NAME, Key=key)['Body'].read()
    hospitals = json.loads(body)
    print(f'Loaded {len(hospitals)} hospitals')
    print('First:', hospitals[0])
except Exception as e:
    import traceback
    traceback.print_exc()
