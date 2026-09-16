from app.core.s3 import get_s3_client, BUCKET_NAME
import json
import duckdb

client = get_s3_client()
key = 'pipeline-runs/63ec75fb-0619-493d-9eb3-617551347529/hospitals.json'
body = client.get_object(Bucket=BUCKET_NAME, Key=key)['Body'].read()
hospitals = json.loads(body)

for h in hospitals:
    h['run_id'] = '63ec75fb'

try:
    con = duckdb.connect()
    con.execute('CREATE TABLE hospitals AS SELECT * FROM hospitals')
    result = con.execute('SELECT COUNT(*) FROM hospitals').fetchone()
    print(f'Rows in DuckDB: {result[0]}')
    con.close()
except Exception as e:
    import traceback
    traceback.print_exc()
