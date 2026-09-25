import os
import boto3
import tempfile
import pysus
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s3_ENDPOINT = os.getenv("FLOCI_ENDPOINT_URL", "http://floci:4566")
s3_BUCKET = os.getenv("s3_BUCKET_NAME", "datapulse")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

#BR states
BR_STATES = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
]

# CNES TP_UNID mapping to hospital types
TP_UNID_MAP = {
    "01": "Hospital Geral",
    "02": "Hospital Especializado",
    "04": "Unidade de Apoio Diagnose e Terapia",
    "05": "Pronto Socorro Geral",
    "07": "Unidade de Saúde da Família",
    "15": "Unidade Mista",
    "20": "Pronto-Atendimento",
    "21": "Hospital/Dia - Isolado",
    "36": "Clínica Especializada",
    "39": "Unidade de Atenção em Saúde Indígena",
    "69": "Centro de Atenção Psicossocial",
    "70": "Laboratório de Saúde Pública",
    "71": "Centro de Diagnóstico por Imagem",
    "72": "Unidade de Saúde Mental",
    "73": "Pronto-socorro Especializado",
    "74": "Policlínica",
    "75": "Maternidade",
    "76": "Hospital Dia",
    "77": "Banco de Leite Humano",
    "78": "Unidade de Atenção à Saúde Indígena",
    "79": "Oficina Ortopédica",
    "80": "Laboratório de Genética Humana",
    "81": "Central de Regulação de Serviços de Saúde",
    "82": "Unidade de Atenção à Saúde do Trabalhador",
    "83": "Polo de Academia da Saúde",
    "84": "Telessaúde",
    "85": "Centro de Imunização",
}

NATUREZA_MAP = {
    "01": "Administração Pública",
    "02": "Entidades Empresariais",
    "03": "Entidades sem Fins Lucrativos",
    "04": "Pessoas Físicas",
    "05": "Entidades Fechadas de Previdência Privada",
}

def get_s3_client():
    return boto3.client(
       "s3",
        endpoint_url=s3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION, 
    )
    
import os
import boto3
import tempfile
import pysus
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


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def download_cnes_all_states(year: int = 2024, month: int = 12) -> str:
    """Download CNES ST for Brazilian states -> CSV"""
    print(f"Downloading CNES ST data for all {len(BR_STATES)} states...")

    import pandas as pd
    all_dfs = []

    for state in BR_STATES:
        try:
            result = pysus.ftp.cnes(group='ST', state=state, year=year, month=month, source='origin')
            df = result.to_dataframe()
            if df is not None and len(df) > 0:
                df['UF'] = state
                all_dfs.append(df)
                print(f"  {state}: {len(df)} establishments - OK")
            else:
                print(f"  {state}: empty dataframe")
        except Exception as e:
            print(f"  {state}: ERROR - {type(e).__name__}: {e}")

    print(f"States loaded: {len(all_dfs)} of {len(BR_STATES)}")

    if not all_dfs:
        raise ValueError("No state data loaded — check FTP connection")

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Total establishments: {len(combined)}")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    combined.to_csv(tmp.name, index=False)
    tmp.close()

    s3 = get_s3_client()
    s3_key = f"brazil/raw/cnes_estabelecimentos_{year}{month:02d}.csv"
    with open(tmp.name, 'rb') as f:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
    print(f"Uploaded to S3: {s3_key}")

    os.unlink(tmp.name)
    return s3_key


def process_with_spark(s3_key: str):
    """Process with PySpark -> save as Parquet"""
    print("Starting Spark job...")

    spark = SparkSession.builder \
        .appName("DataPulse-DATASUS-BR") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    s3 = get_s3_client()
    obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
    csv_content = obj["Body"].read().decode("utf-8")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    tmp.write(csv_content.encode())
    tmp.close()
    tmp_path = tmp.name

    try:
        df = spark.read.csv(tmp_path, header=True, inferSchema=False)
        print(f"Total records: {df.count()}")

        df = df.select(
            F.col("CNES").alias("facility_id"),
            F.col("CODUFMUN").alias("municipality_code"),
            F.col("COD_CEP").alias("zip_code"),
            F.col("UF").alias("state"),
            F.col("TP_UNID").alias("hospital_type_code"),
            F.col("NATUREZA").alias("ownership_code"),
            F.col("VINC_SUS").alias("vinc_sus"),
            F.col("URGEMERG").alias("emergency_services_raw"),
            F.col("LEITHOSP").alias("hospital_beds"),
            F.col("TURNO_AT").alias("operation_hours"),
            F.col("COMPETEN").alias("competencia"),
        ) \
        .withColumn("country", F.lit("BR")) \
        .withColumn("facility_name", F.concat(F.lit("CNES "), F.col("facility_id"))) \
        .withColumn("emergency_services", F.when(F.col("emergency_services_raw") == "1", "Sim").otherwise("Não")) \
        .withColumn("address", F.lit(None).cast("string")) \
        .withColumn("city", F.col("municipality_code")) \
        .withColumn("overall_rating", F.lit(None).cast("integer")) \
        .withColumn("normalized_score", F.lit(None).cast("double")) \
        .withColumn("rating_system", F.lit("CNES — dados estruturais")) \
        .withColumn("raw_rating_label", F.lit(None).cast("string"))

        local_parquet = "/tmp/datasus-br"
        df.write \
            .mode("overwrite") \
            .partitionBy("country", "state") \
            .parquet(local_parquet)

        s3 = get_s3_client()
        for root, dirs, files in os.walk(local_parquet):
            for file in files:
                if file.endswith(".parquet"):
                    local_file = os.path.join(root, file)
                    relative = os.path.relpath(local_file, local_parquet)
                    s3_key_out = f"hospitals/processed/{relative}".replace("\\", "/")
                    with open(local_file, "rb") as f:
                        s3.put_object(Bucket=S3_BUCKET, Key=s3_key_out, Body=f.read())
                    print(f"parquet_uploaded key={s3_key_out}")

    finally:
        os.unlink(tmp_path)
        spark.stop()
        print("Spark job complete")


if __name__ == "__main__":
    s3_key = download_cnes_all_states(year=2024, month=12)
    process_with_spark(s3_key)    

