import boto3
import tempfile
import os
import duckdb
import math
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.s3 import get_s3_client, BUCKET_NAME
from app.schemas.hospital import Hospital as HospitalSchema
from app.repositories.hospital_repository import save_hospitals
from app.core.country_normalizer import normalize_score, get_rating_systems


def _load_br_hospitals_from_parquet(state: str | None = None) -> list[dict]:
    """Load Brazilian hospitals from Parquet in S3."""
    client = get_s3_client()
    prefix = "hospitals/processed/country=BR/"
    if state:
        prefix += f"state={state}/"

    response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    objects = response.get("Contents", [])
    parquet_files = [obj["Key"] for obj in objects if obj["Key"].endswith(".parquet")]

    if not parquet_files:
        return []

    file_state_map = {}
    tmp_files = []
    for key in parquet_files:
        body = client.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
        tmp.write(body)
        tmp.close()
        tmp_files.append(tmp.name)
        parts = key.split("/")
        state_part = next((p for p in parts if p.startswith("state=")), "state=")
        file_state_map[tmp.name] = state_part.replace("state=", "")

    try:
        import pandas as pd
        all_dfs = []
        for tmp_file in tmp_files:
            state_val = file_state_map[tmp_file]
            con = duckdb.connect()
            df = con.execute(f"""
                SELECT
                    facility_id,
                    facility_name,
                    address,
                    city,
                    '{state_val}' AS state,
                    zip_code,
                    hospital_type,
                    hospital_ownership,
                    emergency_services,
                    telephone_number,
                    latitude,
                    longitude,
                    'BR' AS country,
                    rating_system,
                    raw_rating_label,
                    overall_rating,
                    normalized_score
                FROM read_parquet('{tmp_file}')
            """).fetchdf()
            con.close()
            all_dfs.append(df)

        result = pd.concat(all_dfs, ignore_index=True)
        return result.to_dict(orient="records")
    finally:
        for f in tmp_files:
            os.unlink(f)


async def ingest_br_hospitals(session: AsyncSession) -> int:
    """Ingest Brazilian hospitals from DATASUS Parquet into PostgreSQL."""
    logger.info("datasus_ingest_start")

    rows = _load_br_hospitals_from_parquet()
    if not rows:
        logger.error("datasus_no_parquet_data")
        raise ValueError("No Brazilian hospital data found in S3. Run the DATASUS Spark job first.")

    logger.info("datasus_parquet_loaded", count=len(rows))

    hospitals = []
    for row in rows:
        try:
            hospital = HospitalSchema(
                facility_id=f"BR-{row['facility_id']}",
                facility_name=row.get("facility_name") or f"CNES {row['facility_id']}",
                address=row.get("address") if isinstance(row.get("address"), str) else "",
                city=row.get("city") if isinstance(row.get("city"), str) else str(row.get("city", "")),
                state=row.get("state") or "",
                zip_code=row.get("zip_code") if isinstance(row.get("zip_code"), str) else "",
                hospital_type=row.get("hospital_type") if isinstance(row.get("hospital_type"), str) else "",
                hospital_ownership=row.get("hospital_ownership") if isinstance(row.get("hospital_ownership"), str) else "",
                emergency_services=row.get("emergency_services") if isinstance(row.get("emergency_services"), str) else "Não",
                overall_rating=None,
                telephone_number=row.get("telephone_number") if isinstance(row.get("telephone_number"), str) else None,
                latitude=float(row["latitude"]) if row.get("latitude") and not (isinstance(row.get("latitude"), float) and math.isnan(row["latitude"])) else None,
                longitude=float(row["longitude"]) if row.get("longitude") and not (isinstance(row.get("longitude"), float) and math.isnan(row["longitude"])) else None,
                country="BR",
                normalized_score=None,
                rating_system=get_rating_systems("BR"),
                raw_rating_label=None,
            )
            hospitals.append(hospital)
        except Exception as e:
            logger.error("datasus_hospital_parse_error", error=str(e), row=str(row)[:100])

    await save_hospitals(session, hospitals)
    logger.info("datasus_ingest_complete", count=len(hospitals))
    return len(hospitals)