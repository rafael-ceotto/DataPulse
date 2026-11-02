import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.models.patient_experience import HospitalPatientExperience

logger = logging.getLogger(__name__)

DATASET_IDENTIFIER = "dgck-syfz"  # "Patient survey (HCAHPS) - Hospital" — confirmed via metastore, count=325720
BASE_URL = f"https://data.cms.gov/provider-data/api/1/datastore/query/{DATASET_IDENTIFIER}/0"
PAGE_SIZE = 1500  # CMS API hard max

# Ordered prefix rules — confirmed exhaustive against the real 68 distinct hcahps_measure_id values
# (no "other" bucket should ever be hit; a logger.warning means the CMS schema changed).
_CATEGORY_RULES: list[tuple[str, str]] = [
    ("H_COMP_1", "nurse_communication"),
    ("H_NURSE_RESPECT", "nurse_communication"),
    ("H_NURSE_LISTEN", "nurse_communication"),
    ("H_NURSE_EXPLAIN", "nurse_communication"),
    ("H_COMP_2", "doctor_communication"),
    ("H_DOCTOR_RESPECT", "doctor_communication"),
    ("H_DOCTOR_LISTEN", "doctor_communication"),
    ("H_DOCTOR_EXPLAIN", "doctor_communication"),
    ("H_COMP_5", "medication_communication"),
    ("H_MED_FOR", "medication_communication"),
    ("H_SIDE_EFFECTS", "medication_communication"),
    ("H_COMP_6", "discharge_information"),
    ("H_DISCH_HELP", "discharge_information"),
    ("H_SYMPTOMS", "discharge_information"),
    ("H_CLEAN", "cleanliness"),
    ("H_QUIET", "quietness"),
    ("H_HSP_RATING", "overall_rating"),
    ("H_RECMND", "recommend_hospital"),
    ("H_STAR_RATING", "summary"),
]


def categorize(measure_id: str) -> str:
    for prefix, category in _CATEGORY_RULES:
        if measure_id.startswith(prefix):
            return category
    logger.warning("Unrecognized hcahps_measure_id prefix, bucketed as 'other': %s", measure_id)
    return "other"


def is_star_rating(measure_id: str) -> bool:
    return measure_id.endswith("_STAR_RATING") or measure_id == "H_STAR_RATING"


async def fetch_all_rows() -> list[dict]:
    rows: list[dict] = []
    offset = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            resp = await client.get(BASE_URL, params={"limit": PAGE_SIZE, "offset": offset})
            resp.raise_for_status()
            payload = resp.json()
            page = payload.get("results", [])
            rows.extend(page)
            total = payload.get("count", len(rows))
            print(f"Fetched {len(rows)}/{total} rows (offset={offset})")
            if len(page) < PAGE_SIZE or len(rows) >= total:
                break
            offset += PAGE_SIZE
    return rows


async def upsert_rows(rows: list[dict]) -> None:
    async with AsyncSessionLocal() as session:
        for i in range(0, len(rows), 500):
            batch = rows[i : i + 500]
            values = [
                {
                    "facility_id": r["facility_id"],
                    "hcahps_measure_id": r["hcahps_measure_id"],
                    "hcahps_question": r.get("hcahps_question"),
                    "hcahps_answer_description": r.get("hcahps_answer_description"),
                    "patient_experience_category": categorize(r["hcahps_measure_id"]),
                    "is_star_rating": is_star_rating(r["hcahps_measure_id"]),
                    "star_rating": r.get("patient_survey_star_rating"),
                    "answer_percent": r.get("hcahps_answer_percent"),
                    "linear_mean_value": r.get("hcahps_linear_mean_value"),
                    "number_of_completed_surveys": r.get("number_of_completed_surveys"),
                    "survey_response_rate_percent": r.get("survey_response_rate_percent"),
                    "start_date": r.get("start_date"),
                    "end_date": r.get("end_date"),
                }
                for r in batch
                if r.get("facility_id") and r.get("hcahps_measure_id")
            ]
            if not values:
                continue
            stmt = pg_insert(HospitalPatientExperience).values(values)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_patient_experience_facility_measure",
                set_={
                    "hcahps_question": stmt.excluded.hcahps_question,
                    "hcahps_answer_description": stmt.excluded.hcahps_answer_description,
                    "patient_experience_category": stmt.excluded.patient_experience_category,
                    "is_star_rating": stmt.excluded.is_star_rating,
                    "star_rating": stmt.excluded.star_rating,
                    "answer_percent": stmt.excluded.answer_percent,
                    "linear_mean_value": stmt.excluded.linear_mean_value,
                    "number_of_completed_surveys": stmt.excluded.number_of_completed_surveys,
                    "survey_response_rate_percent": stmt.excluded.survey_response_rate_percent,
                    "start_date": stmt.excluded.start_date,
                    "end_date": stmt.excluded.end_date,
                },
            )
            await session.execute(stmt)
        await session.commit()
    print(f"Upserted {len(rows)} rows into hospital_patient_experience.")


async def main() -> None:
    rows = await fetch_all_rows()
    print(f"Total rows fetched from CMS: {len(rows)}")
    await upsert_rows(rows)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())