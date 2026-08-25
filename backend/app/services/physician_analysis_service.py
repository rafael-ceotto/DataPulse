import asyncio
import json as json_lib
import urllib.request

import httpx
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache, set_cache
from app.models.hospital import Hospital as HospitalModel

CMS_PHYSICIAN_API = "https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0"
CACHE_KEY = "physician_state_counts"
CACHE_TTL = 86400
NATIONAL_SPECIALTY_CACHE_KEY = "national_specialty_counts"
NATIONAL_SPECIALTY_TTL = 86400


async def get_physician_counts_by_state() -> dict:
    cached = await get_cache(CACHE_KEY)
    if cached:
        return cached

    counts = {}
    limit = 1500
    offset = 0
    total = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            url = f"{CMS_PHYSICIAN_API}?limit={limit}&offset={offset}&properties%5B%5D=npi&properties%5B%5D=state"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            if total is None:
                total = data.get("count", 0)

            results = data.get("results", [])
            if not results:
                break

            for r in results:
                state = r.get("state", "")
                if state:
                    counts[state] = counts.get(state, 0) + 1

            offset += limit
            if offset >= total:
                break

    await set_cache(CACHE_KEY, counts, ttl=CACHE_TTL)
    return counts


async def get_physician_hospital_correlation(session: AsyncSession) -> list[dict]:
    physician_counts = await get_physician_counts_by_state()

    result = await session.execute(
        select(
            HospitalModel.state,
            func.avg(HospitalModel.overall_rating).label("avg_rating"),
            func.count(HospitalModel.facility_id).label("hospital_count"),
        )
        .where(HospitalModel.overall_rating.isnot(None))
        .group_by(HospitalModel.state)
    )

    hospital_data = [
        {
            "state": r.state,
            "avg_rating": round(float(r.avg_rating), 2),
            "hospital_count": r.hospital_count,
        }
        for r in result
    ]

    hospital_df = pd.DataFrame(hospital_data)
    physician_df = pd.DataFrame(
        [{"state": k, "physician_count": v} for k, v in physician_counts.items()]
    )

    merged = pd.merge(physician_df, hospital_df, on="state", how="inner")
    merged["physicians_per_hospital"] = (
        merged["physician_count"] / merged["hospital_count"]
    ).round(1)

    return (
        merged.sort_values("avg_rating", ascending=False)
        .to_dict(orient="records")
    )


async def search_physicians(
    state: str | None = None,
    specialty: str | None = None,
    name: str | None = None,
    limit: int = 20,
) -> dict:
    conditions = []

    if state:
        conditions.append({"property": "state", "value": state, "operator": "="})
    if specialty:
        conditions.append({"property": "pri_spec", "value": specialty.upper(), "operator": "="})
    if name:
        conditions.append({"property": "provider_last_name", "value": name.upper(), "operator": "LIKE"})

    query_parts = [f"limit={limit}&offset=0"]
    for i, c in enumerate(conditions):
        query_parts.append(
            f"conditions%5B{i}%5D%5Bproperty%5D={c['property']}"
            f"&conditions%5B{i}%5D%5Bvalue%5D={c['value']}"
            f"&conditions%5B{i}%5D%5Boperator%5D={c['operator']}"
        )

    url = f"{CMS_PHYSICIAN_API}?{'&'.join(query_parts)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        request = httpx.Request("GET", httpx.URL(url))
        response = await client.send(request)
        response.raise_for_status()
        data = response.json()

    return {
        "total": data.get("count", 0),
        "results": [
            {
                "npi": r.get("npi"),
                "name": f"{r.get('provider_first_name', '')} {r.get('provider_last_name', '')}".strip(),
                "gender": r.get("gndr"),
                "credentials": r.get("cred"),
                "specialty": r.get("pri_spec"),
                "city": r.get("citytown"),
                "state": r.get("state"),
                "zip_code": r.get("zip_code"),
                "telephone": r.get("telephone_number"),
                "facility": r.get("facility_name"),
                "telehealth": r.get("telehlth") == "Y",
            }
            for r in data.get("results", [])
        ],
    }


async def get_national_specialty_counts() -> dict:
    cached = await get_cache(NATIONAL_SPECIALTY_CACHE_KEY)
    if cached:
        return cached

    counts = {}
    limit = 1500
    SAMPLE_SIZE = 50000  # ~1.5% of total — statistically significant
    offset = 0
    total_fetched = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        while total_fetched < SAMPLE_SIZE:
            url = f"{CMS_PHYSICIAN_API}?limit={limit}&offset={offset}&properties%5B%5D=npi&properties%5B%5D=pri_spec"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                break

            for r in results:
                spec = r.get("pri_spec", "").strip()
                if spec:
                    counts[spec] = counts.get(spec, 0) + 1

            total_fetched += len(results)
            offset += limit

    # Scale up to estimated national total (3.3M / 50k = ~66x)
    TOTAL_PHYSICIANS = 3388151
    scale_factor = TOTAL_PHYSICIANS / total_fetched
    counts = {k: round(v * scale_factor) for k, v in counts.items()}

    print(f"Finished! Sampled {total_fetched} records, estimated national counts for {len(counts)} specialties")
    await set_cache(NATIONAL_SPECIALTY_CACHE_KEY, counts, ttl=NATIONAL_SPECIALTY_TTL)
    return counts


async def get_scarce_specialties(state: str) -> list[dict]:
    cache_key = f"scarce_specialties:{state}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    # Check if national cache is ready
    national_counts = await get_cache(NATIONAL_SPECIALTY_CACHE_KEY)
    if not national_counts:
        return [{
            "error": "National specialty cache not ready",
            "message": "Call POST /api/v1/physicians/warm-cache first and wait a few minutes"
        }]

    all_results = []
    limit = 1500
    offset = 0
    total = None
    loop = asyncio.get_event_loop()

    while True:
        url = (
            f"{CMS_PHYSICIAN_API}"
            f"?limit={limit}&offset={offset}"
            f"&properties%5B%5D=npi&properties%5B%5D=pri_spec"
            f"&conditions%5B0%5D%5Bproperty%5D=state"
            f"&conditions%5B0%5D%5Bvalue%5D={state}"
            f"&conditions%5B0%5D%5Boperator%5D=%3D"
        )

        def fetch(u):
            import http.client
            import ssl
            host = "data.cms.gov"
            path_and_query = u.replace("https://data.cms.gov", "")
            context = ssl.create_default_context()
            conn = http.client.HTTPSConnection(host, timeout=60, context=context)
            conn.request("GET", path_and_query)
            r = conn.getresponse()
            body = r.read()
            if r.status != 200:
                raise Exception(f"HTTP {r.status}: {body}")
            return json_lib.loads(body)

        data = await loop.run_in_executor(None, fetch, url)

        if total is None:
            total = data.get("count", 0)

        results = data.get("results", [])
        if not results:
            break

        all_results.extend(results)
        offset += limit
        if offset >= total:
            break

    if not all_results:
        return []

    state_df = pd.DataFrame(all_results)
    state_counts = (
        state_df.groupby("pri_spec")
        .size()
        .reset_index(name="state_count")
    )

    EXPECTED_SHARE = 1 / 56

    results = []
    for _, row in state_counts.iterrows():
        spec = row["pri_spec"]
        state_count = int(row["state_count"])
        national_count = national_counts.get(spec, 0)

        if national_count == 0:
            continue

        national_share = state_count / national_count
        scarcity_ratio = national_share / EXPECTED_SHARE

        if scarcity_ratio < 0.5:
            results.append({
                "specialty": spec,
                "state_count": state_count,
                "national_count": national_count,
                "state_share_pct": round(national_share * 100, 2),
                "expected_share_pct": round(EXPECTED_SHARE * 100, 2),
                "scarcity_ratio": round(scarcity_ratio, 3),
                "gap": round((EXPECTED_SHARE - national_share) * national_count),
            })

    results.sort(key=lambda x: x["scarcity_ratio"])
    top10 = results[:10]
    await set_cache(cache_key, top10, ttl=3600)
    return top10