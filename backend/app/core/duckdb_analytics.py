import json
import duckdb
import pandas as pd
from app.core.s3 import get_s3_client, BUCKET_NAME


def _load_runs_from_s3() -> pd.DataFrame:
    """Download all pipeline run JSONs from S3 and return as DataFrame with run_id."""
    client = get_s3_client()
    response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="pipeline-runs/")
    objects = response.get("Contents", [])

    all_rows = []
    for obj in objects:
        key = obj["Key"]
        if not key.endswith("hospitals.json"):
            continue

        parts = key.split("/")
        if len(parts) != 3:
            continue
        run_id = parts[1]

        body = client.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
        hospitals = json.loads(body)

        for hospital in hospitals:
            hospital["run_id"] = run_id

        all_rows.extend(hospitals)

    if not all_rows:
        return pd.DataFrame()

    return pd.DataFrame(all_rows)


def query_historical(sql: str) -> list[dict]:
    """
    Run a DuckDB SQL query over all pipeline run snapshots.
    The data is available as a table called 'hospitals'.
    Columns: facility_id, facility_name, city, state, zip_code,
             hospital_type, hospital_ownership, emergency_services,
             overall_rating, telephone_number, run_id
    """
    df = _load_runs_from_s3()
    if df.empty:
        return []

    con = duckdb.connect()
    con.register("hospitals", df)
    result = con.execute(sql).fetchdf()
    con.close()

    return result.to_dict(orient="records")


def get_rating_trend() -> list[dict]:
    """Average rating per pipeline run, ordered by run_id."""
    return query_historical("""
        SELECT
            run_id,
            ROUND(AVG(overall_rating), 3) AS avg_rating,
            COUNT(*) AS total_hospitals,
            COUNT(CASE WHEN overall_rating IS NOT NULL THEN 1 END) AS rated_hospitals
        FROM hospitals
        GROUP BY run_id
        ORDER BY run_id
    """)


def get_rating_changes() -> list[dict]:
    """States where average rating changed most across runs."""
    return query_historical("""
        WITH state_runs AS (
            SELECT
                run_id,
                state,
                ROUND(AVG(overall_rating), 3) AS avg_rating
            FROM hospitals
            WHERE overall_rating IS NOT NULL
            GROUP BY run_id, state
        ),
        first_last AS (
            SELECT
                state,
                FIRST(avg_rating ORDER BY run_id) AS first_rating,
                LAST(avg_rating ORDER BY run_id) AS last_rating,
                COUNT(DISTINCT run_id) AS num_runs
            FROM state_runs
            GROUP BY state
        )
        SELECT
            state,
            first_rating,
            last_rating,
            ROUND(last_rating - first_rating, 3) AS delta,
            num_runs
        FROM first_last
        WHERE num_runs > 1
        ORDER BY ABS(delta) DESC
        LIMIT 20
    """)


def get_hospital_appearances() -> list[dict]:
    """Hospitals that appeared or disappeared across runs."""
    return query_historical("""
        SELECT
            facility_id,
            facility_name,
            state,
            COUNT(DISTINCT run_id) AS appearances,
            MIN(overall_rating) AS min_rating,
            MAX(overall_rating) AS max_rating
        FROM hospitals
        GROUP BY facility_id, facility_name, state
        HAVING COUNT(DISTINCT run_id) < (SELECT COUNT(DISTINCT run_id) FROM hospitals)
        ORDER BY appearances ASC
        LIMIT 20
    """)
    
def get_scarce_specialties_from_parquet(state:str) -> list[dict]:
    """Read physician specialty Parquet from S3"""
    """Return top-k(10) scarce specialties for state"""
    """Requires PySpark job to run first"""
    client =  get_s3_client()
    prefix = f"physicians/processed/specialties/state={state}"
    
    #If parquet -> True
    response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    objects = response.get("Contents", [])
    parquet_files = [obj["Key"] for obj in objects if obj["Key"].endswith(".parquet")]
    if not parquet_files:
        return []
    
    #2nd -> Download file to temp
    import tempfile
    import os
    
    tmp_files = []
    for key in parquet_files:
        body = client.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
        tmp.write(body)
        tmp.close()
        tmp_files.append(tmp.name)
    
    try:
        con = duckdb.connect()
        files_str = ", ".join([f"'{f}'" for f in tmp_files])
        result = con.execute(f"""
            SELECT
                specialty,
                state_count,
                national_count,
                ROUND(CAST(state_count AS DOUBLE) / national_count * 100, 2) AS state_share_pct,
                ROUND(1.0 / 56 * 100, 2) AS expected_share_pct,
                ROUND(scarcity_ratio, 3) AS scarcity_ratio,
                gap
            FROM read_parquet([{files_str}])
            WHERE scarcity_ratio < 0.5
            ORDER BY scarcity_ratio ASC
            LIMIT 10
        """).fetchdf()
        con.close()
        return result.to_dict(orient="records")
    finally:
        for f in tmp_files:
            os.unlink(f)