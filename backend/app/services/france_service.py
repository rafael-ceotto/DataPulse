import io
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.s3 import get_s3_client, BUCKET_NAME
from app.schemas.hospital import Hospital as HospitalSchema
from app.repositories.hospital_repository import save_hospitals
from app.core.country_normalizer import get_rating_system


async def ingest_fr_hospitals(session: AsyncSession) -> int:
    """Ingest French FINESS hospitals from S3 CSV into PostgreSQL."""
    logger.info("france_ingest_start")

    client = get_s3_client()
    s3_key = "hospitals/processed/country=FR/finess_hospitals.csv"

    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))
    except Exception as e:
        logger.error("france_csv_not_found", error=str(e))
        raise ValueError("No French hospital data found in S3. Run the France processor first.")

    logger.info("france_csv_loaded", count=len(df))

    hospitals = []
    for _, row in df.iterrows():
        try:
            hospital = HospitalSchema(
                facility_id=f"FR-{row['facility_id']}",
                facility_name=str(row.get("facility_name") or ""),
                address=str(row.get("address") or ""),
                city=str(row.get("city") or ""),
                state=str(row.get("state") or "France"),
                zip_code=str(row.get("zip_code") or ""),
                hospital_type=str(row.get("hospital_type") or ""),
                hospital_ownership=str(row.get("hospital_ownership") or ""),
                emergency_services=str(row.get("emergency_services") or ""),
                overall_rating=None,
                telephone_number=str(row["telephone_number"]) if pd.notna(row.get("telephone_number")) else None,
                latitude=float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
                longitude=float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
                country="FR",
                normalized_score=None,
                rating_system=get_rating_system("FR"),
                raw_rating_label=None,
            )
            hospitals.append(hospital)
        except Exception as e:
            logger.error("france_hospital_parse_error", error=str(e))

    await save_hospitals(session, hospitals)
    logger.info("france_ingest_complete", count=len(hospitals))
    return len(hospitals)