import os
import httpx
import boto3
import io
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


#S3 config
S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://localhost:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
CMS_PHYSICIANS_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0"
RAW_S3_KEY = "physicians/raw/physicians.csv"
PROCESSED_S3_PREFIX = "physicians/processed/specialties"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url = S3_ENDPOINT,
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
        region_name = AWS_REGION,
    )
    
def download_physicians_to_s3():
    #Download full CMS physicians dataset to S3 as CSV.
    print("physicians_download_start")
    s3 = get_s3_client()
    offset = 0
    limit = 1000
    all_rows = []
    
    with httpx.Client(timeout=60.0) as client:
        while True:
            params =  {"limit": limit, "offset": offset}
            res = client.get(CMS_PHYSICIANS_URL, params=params)
            res.raise_for_status()
            data = res.json()
            results = data.get("results", [])
            if not results:
                break
            all_rows.extend(results)
            offset+=limit
            print(f"physicians_download_progress fetched={len(all_rows)}")
            if len(results) < limit:
                break
            
    print(f"physicians_download_complete total={len(all_rows)}")
    
    if not all_rows:
        raise ValueError("No physician data fetched")
    
    #CSV conversion
    import csv
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
    csv_bytes = output.getvalue().encode("utf-8")
    s3.put_object(Bucket=S3_BUCKET, Key=RAW_S3_KEY, Body=csv_bytes)
    print(f"physicians_uploaded_to_s3 key={RAW_S3_KEY}")
    
def process_with_spark():
    """Process physicians CSV with PySpark and save as Parquet"""
    print("spark_job_start")
    spark = SparkSession.builder \
        .appName("DataPulse-Physicians") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    
    #CSV from S3 to a local temp file
    s3 = get_s3_client()
    obj = s3.get_object(Bucket=S3_BUCKET, Key=RAW_S3_KEY)
    csv_content = obj["Body"].read().decode("utf-8")
    
    tmp_path = "/tmp/physicians.csv"
    with open(tmp_path, "w") as f:
        f.write(csv_content)
    
    print(f"spark_reading_csv path={tmp_path}")
    df = spark.read.csv(tmp_path, header=True, inferSchema=False)
    print(f"spark_total_records count={df.count()}")
    
    #Rename columns
    df = df.withColumnRenamed("pri_spec", "specialty") \
           .withColumnRenamed("nppes_provider_state", "state")
           
    #Filter valid records
    df = df.filter(F.col("specialty").isNotNull() & F.col("state").isNotNull())
    
    #State counts per specialty
    state_counts = df.groupBy("state", "specialty") \
                   .agg(F.count("*").alias("state_count"))
                   
    #National counts per specilty
    national_counts = df.groupBy("specialty") \
                      .agg(F.count("*").alias("national_count"))
                      
    #Join -> Calculate scarcity ratio
    #Share expected: 1/56 (states + DC + territories)    
    result = state_counts.join(national_counts, on="specialty") \
                         .withColumn("expected_count", (F.col("national_count") / 56 ).cast("double")) \
                         .withColumn("scarcity_ratio", F.col("state_count") / F.col("expected_count")) \
                         .withColumn("gap", (F.col("expected_count") - F.col("state_count")).cast("integer") )
    print("spark_writing_parquet")
    
    #Save as Parquet first -> S3
    local_parquet = "/tmp/physician-specialties"
    result.write.mode("overwrite").partitionBy("state").parquet(local_parquet)
    
    #Upload files to S3
    import os
    for root, dirs, files in os.walk(local_parquet):
        for file in files:
            if file.endswith(".parquet"):
                local_file = os.path.join(root, file)
                relative = os.path.relpath(local_file, local_parquet)
                s3_key = f"{PROCESSED_S3_PREFIX}/{relative}".replace("\\", "/")
                with open(local_file, "rb") as f:
                    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
                print(f"parquet_uploaded key={s3_key}")
    spark.stop()
    print("spark_job_complete")
    
if __name__ == "__main__":
    download_physicians_to_s3()
    process_with_spark()
                    
    