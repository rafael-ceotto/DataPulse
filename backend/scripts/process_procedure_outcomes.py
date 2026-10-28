import asyncio, logging, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from httpx import AsyncClient
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.core.database import AsyncSessionLocal
from app.models.procedure_outcomes import HospitalProcedureOutcome

logger = logging.getLogger(__name__)

# NOTE: confirm this is still the live distribution id before trusting it —
# CMS rotates dataset/distribution identifiers over time. This is the one
# documented for "Unplanned Hospital Visits - Hospital". First thing to check
# when this script runs: does the logged total count look like a real
# national hospital dataset (thousands of rows), not some tiny stale number?
DATASET_DISTRIBUTION_ID = "632h-zaca"
BASE_URL = f"https://data.cms.gov/provider-data/api/1/datastore/query/{DATASET_DISTRIBUTION_ID}/0"
PAGE_SIZE = 1500

CATEGORY_RULES: list[tuple[str, str]] = [
    ("MORT_30_AMI", "heart_attack"),
    ("READM_30_AMI", "heart_attack"),
    ("EDAC_30_AMI", "heart_attack"),
    ("MORT_30_HF", "heart_failure"),
    ("READM_30_HF", "heart_failure"),
    ("EDAC_30_HF", "heart_failure"),
    ("MORT_30_PN", "pneumonia"),
    ("READM_30_PN", "pneumonia"),
    ("EDAC_30_PN", "pneumonia"),
    ("MORT_30_COPD", "copd"),
    ("READM_30_COPD", "copd"),
    ("MORT_30_STK", "stroke"),
    ("READM_30_STK", "stroke"),
    ("MORT_30_CABG", "cabg"),
    ("READM_30_CABG", "cabg"),
    ("READM_30_HIP_KNEE", "hip_knee_replacement"),
    ("COMP_HIP_KNEE", "hip_knee_replacement"),
    ("PSI_90", "patient_safety"),
    ("READM_30_HOSP_WIDE", "readmission_overall"),
    ("Hybrid_HWR", "readmission_overall"),
    ("OP_32", "outpatient_visit_followup"),
    ("OP_35", "outpatient_visit_followup"),
    ("OP_36", "outpatient_visit_followup"),
    ("OP_37", "outpatient_visit_followup"),
    ("REH_OP_36", "outpatient_visit_followup"),
]


def categorize(measure_id: str) -> str:
    for prefix, category in CATEGORY_RULES:
        if measure_id.startswith(prefix):
            return category
    logger.warning("Unrecognized measure_id prefix, bucketed as 'other': %s", measure_id)
    return "other"


async def fetch_all_rows() -> list[dict]:
    rows: list[dict] = []
    offset = 0
    async with AsyncClient(timeout=30.0) as client:
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
                    "measure_id": r["measure_id"],
                    "measure_name": r["measure_name"],
                    "procedure_category": categorize(r["measure_id"]),
                    "compared_to_national": r.get("compared_to_national"),
                    "denominator": r.get("denominator"),
                    "score": r.get("score"),
                    "lower_estimate": r.get("lower_estimate"),
                    "higher_estimate": r.get("higher_estimate"),
                    "number_of_patients": r.get("number_of_patients"),
                    "number_of_patients_returned": r.get("number_of_patients_returned"),
                    "footnote": r.get("footnote"),
                    "start_date": r.get("start_date"),
                    "end_date": r.get("end_date"),
                }
                for r in batch
                if r.get("facility_id") and r.get("measure_id")
            ]
            if not values:
                continue
            stmt = pg_insert(HospitalProcedureOutcome).values(values)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_procedure_outcome_facility_measure",
                set_={
                    "measure_name": stmt.excluded.measure_name,
                    "procedure_category": stmt.excluded.procedure_category,
                    "compared_to_national": stmt.excluded.compared_to_national,
                    "denominator": stmt.excluded.denominator,
                    "score": stmt.excluded.score,
                    "lower_estimate": stmt.excluded.lower_estimate,
                    "higher_estimate": stmt.excluded.higher_estimate,
                    "number_of_patients": stmt.excluded.number_of_patients,
                    "number_of_patients_returned": stmt.excluded.number_of_patients_returned,
                    "footnote": stmt.excluded.footnote,
                    "start_date": stmt.excluded.start_date,
                    "end_date": stmt.excluded.end_date,
                },
            )
            await session.execute(stmt)
        await session.commit()
    print(f"Upserted {len(rows)} rows into hospital_procedure_outcomes.")


async def main() -> None:
    rows = await fetch_all_rows()
    print(f"Total rows fetched from CMS: {len(rows)}")
    await upsert_rows(rows)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())