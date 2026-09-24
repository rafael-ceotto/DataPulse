import duckdb
import boto3
import tempfile
import os

import duckdb
import boto3
import tempfile
import os

client = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

obj = client.get_object(
    Bucket='datapulse',
    Key='physicians/processed/specialties/state=OH/part-00000-e56baaf3-7ed4-467b-bfbc-b75bac3ca53a.c000.snappy.parquet'
)

tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.parquet')
tmp.write(obj['Body'].read())
tmp.close()

con = duckdb.connect()
result = con.execute(f"SELECT specialty, COUNT(*) as cnt FROM read_parquet('{tmp.name}') GROUP BY specialty ORDER BY cnt DESC LIMIT 10").fetchdf()
print(result)
print(f"Total rows: {con.execute(f'SELECT COUNT(*) FROM read_parquet(\'{tmp.name}\')').fetchone()[0]}")
os.unlink(tmp.name)