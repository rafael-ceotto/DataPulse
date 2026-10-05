import io
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.core.s3 import get_s3_client, BUCKET_NAME
from app.schemas.hospital import Hospital as HospitalSchema
from app.repositories.hospital_repository import save_hospitals
from app.core.country_normalizer import get_rating_systems


async def ingest_es_hospitals(session: AsyncSession) -> int:
    """Ingest Spanish hospitals from S3 CSV into PostgreSQL."""
    logger.info("spain_ingest_start")

    client = get_s3_client()
    s3_key = "hospitals/processed/country=ES/spain_hospitals.csv"

    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()), keep_default_na=False, encoding='utf-8-sig')
    except Exception as e:
        logger.error("spain_csv_not_found", error=str(e))
        raise ValueError("No Spanish hospital data found in S3. Run the Spain processor first.")

    logger.info("spain_csv_loaded", count=len(df))

    hospitals = []
    for _, row in df.iterrows():
        try:
            hospital = HospitalSchema(
                facility_id=f"ES-{row['facility_id']}",
                facility_name=str(row.get("facility_name") or ""),
                address=str(row.get("address") or ""),
                city=str(row.get("city") or ""),
                state=str(row.get("state") or "España"),
                zip_code=str(row.get("zip_code") or ""),
                hospital_type=str(row.get("hospital_type") or "Hospital"),
                hospital_ownership=str(row.get("hospital_ownership") or ""),
                emergency_services="",
                overall_rating=None,
                telephone_number=str(row["telephone_number"]) if str(row.get("telephone_number", "")) not in ["nan", "", "None"] else None,
                latitude=float(row["latitude"]) if str(row.get("latitude", "")) not in ["nan", "", "None"] else None,
                longitude=float(row["longitude"]) if str(row.get("longitude", "")) not in ["nan", "", "None"] else None,
                country="ES",
                normalized_score=None,
                rating_system=get_rating_systems("ES"),
                raw_rating_label=None,
            )
            hospitals.append(hospital)
        except Exception as e:
            logger.error("spain_hospital_parse_error", error=str(e))

    await save_hospitals(session, hospitals)
    logger.info("spain_ingest_complete", count=len(hospitals))
    return len(hospitals)