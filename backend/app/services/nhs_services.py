import boto3, tempfile, os, io
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.s3 import get_s3_client, BUCKET_NAME
from app.schemas.hospital import Hospital as HospitalSchema
from app.repositories.hospital_repository import save_hospitals
from app.core.country_normalizer import get_rating_systems

async def ingest_gb_hospitals(session: AsyncSession) -> int:
    logger.info("nhs_ingest_start")
    client = get_s3_client()
    s3_key = "hospitals/processed/country=GB/nhs_trusts.csv"
    
    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))
    except Exception as e:
        logger.error("nhs_parquet_not_found", error=str(e))
        raise ValueError("No UK hospital data found in S3. Run NHS processor first.")
    logger.info("nhs_csv_loaded", cound=len(df))
    
    hospitals = []
    for _, row in df.iterrows():
        try:
            hospital=HospitalSchema(
                facility_id=f"GB-{row['facility_id']}",
                facility_name=str(row.get("facility_name") or ""),
                address=str(row.get("address") or ""),
                city=str(row.get("city") or ""),
                state=str(row.get("state") or "England"),
                zip_code=str(row.get("zip_code") or ""),
                hospital_type=str(row.get("hospital_type") or "NHS Trust"),
                hospital_ownership=str(row.get("hospital_ownership") or "NHS"),
                emergency_services=str(row.get("emergency_services") or "") if pd.notna(row.get("emergency_services")) else "",
                overall_rating=None,
                telephone_number=None,
                latitude=float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
                longitude=float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
                country="GB",
                normalized_score=None,
                rating_system=get_rating_systems("GB"),
                raw_rating_label=None,
            )
            hospitals.append(hospital)
        except Exception as e:
            logger.error("nhs_hospital_parse_error", error=str(e))
    await save_hospitals(session, hospitals)
    logger.info("nhs_ingest_complete", count=len(hospitals))
    return len(hospitals)
    