import os
import boto3
import tempfile
import time
import httpx
import pysus
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

S3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

BR_STATES = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
]

CNES_API = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def download_cnes_with_beds(year: int = 2024, month: int = 12) -> pd.DataFrame:
    """Download CNES ST for all states, filter only establishments with hospital beds."""
    print(f"Downloading CNES ST data for all {len(BR_STATES)} states...")
    all_dfs = []

    for state in BR_STATES:
        try:
            result = pysus.ftp.cnes(group='ST', state=state, year=year, month=month, source='origin')
            df = result.to_dataframe()
            df['LEITHOSP'] = pd.to_numeric(df['LEITHOSP'], errors='coerce').fillna(0)
            hospitals = df[df['LEITHOSP'] > 0].copy()
            hospitals['UF'] = state
            all_dfs.append(hospitals)
            print(f"  {state}: {len(df)} total, {len(hospitals)} with beds")
        except Exception as e:
            print(f"  {state}: ERROR - {type(e).__name__}: {e}")

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Total hospitals with beds: {len(combined)}")
    return combined


def fetch_hospital_names(cnes_codes: list) -> dict:
    """Fetch hospital names and addresses from CNES REST API."""
    print(f"Fetching names for {len(cnes_codes)} hospitals from API...")
    names = {}
    
    batch_size = 20
    total_batches = (len(cnes_codes) + batch_size - 1) // batch_size
    
    with httpx.Client(timeout=15.0) as client:
        for i in range(0, len(cnes_codes), batch_size):
            batch = cnes_codes[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if batch_num % 50 == 0:
                print(f"  Batch {batch_num}/{total_batches}...")
            
            for cnes_code in batch:
                try:
                    r = client.get(f"{CNES_API}?limit=1&offset=0", params={"codigo_cnes": cnes_code})
                    if r.status_code == 200:
                        data = r.json()
                        establishments = data.get("estabelecimentos", [])
                        if establishments:
                            e = establishments[0]
                            names[str(cnes_code)] = {
                                "facility_name": e.get("nome_razao_social") or e.get("nome_fantasia") or f"CNES {cnes_code}",
                                "address": f"{e.get('endereco_estabelecimento', '')} {e.get('numero_estabelecimento', '')}".strip(),
                                "city": str(e.get("codigo_municipio", "")),
                                "telephone_number": e.get("numero_telefone_estabelecimento"),
                                "latitude": e.get("latitude_estabelecimento_decimo_grau"),
                                "longitude": e.get("longitude_estabelecimento_decimo_grau"),
                            }
                except Exception as e:
                    pass
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
    
    print(f"Names fetched: {len(names)} of {len(cnes_codes)}")
    return names


def process_with_spark(df: pd.DataFrame, names: dict) -> None:
    """Process DATASUS data with PySpark and save as Parquet."""
    print("Starting Spark job...")

    spark = SparkSession.builder \
        .appName("DataPulse-DATASUS-BR") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Add enriched data from API
    df['facility_name'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('facility_name', f"CNES {x}"))
    df['address'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('address', ''))
    df['city'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('city', df.loc[df['CNES'] == x, 'CODUFMUN'].values[0] if len(df.loc[df['CNES'] == x]) > 0 else ''))
    df['telephone_number'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('telephone_number'))
    df['latitude'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('latitude'))
    df['longitude'] = df['CNES'].apply(lambda x: names.get(str(x), {}).get('longitude'))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    df.to_csv(tmp.name, index=False)
    tmp.close()
    tmp_path = tmp.name

    try:
        sdf = spark.read.csv(tmp_path, header=True, inferSchema=False)
        print(f"Total records: {sdf.count()}")

        sdf = sdf.select(
            F.col("CNES").alias("facility_id"),
            F.col("facility_name"),
            F.col("address"),
            F.col("city"),
            F.col("UF").alias("state"),
            F.col("COD_CEP").alias("zip_code"),
            F.col("TP_UNID").alias("hospital_type"),
            F.col("NATUREZA").alias("hospital_ownership"),
            F.col("URGEMERG").alias("emergency_services_raw"),
            F.col("LEITHOSP").alias("hospital_beds"),
            F.col("telephone_number"),
            F.col("latitude"),
            F.col("longitude"),
        ) \
        .withColumn("country", F.lit("BR")) \
        .withColumn("emergency_services", F.when(F.col("emergency_services_raw") == "1", "Sim").otherwise("Não")) \
        .withColumn("overall_rating", F.lit(None).cast("integer")) \
        .withColumn("normalized_score", F.lit(None).cast("double")) \
        .withColumn("rating_system", F.lit("CNES — dados estruturais")) \
        .withColumn("raw_rating_label", F.lit(None).cast("string"))

        local_parquet = "/tmp/datasus-br"
        sdf.write \
            .mode("overwrite") \
            .partitionBy("country", "state") \
            .parquet(local_parquet)

        s3 = get_s3_client()
        for root, dirs, files in os.walk(local_parquet):
            for file in files:
                if file.endswith(".parquet"):
                    local_file = os.path.join(root, file)
                    relative = os.path.relpath(local_file, local_parquet)
                    s3_key = f"hospitals/processed/{relative}".replace("\\", "/")
                    with open(local_file, "rb") as f:
                        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
                    print(f"parquet_uploaded key={s3_key}")

    finally:
        os.unlink(tmp_path)
        spark.stop()
        print("Spark job complete")


if __name__ == "__main__":    
    df = download_cnes_with_beds(year=2024, month=12)    
    cnes_codes = df['CNES'].tolist()
    names = fetch_hospital_names(cnes_codes)    
    process_with_spark(df, names)