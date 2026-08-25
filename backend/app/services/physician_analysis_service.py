import httpx
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache, set_cache
from app.models.hospital import Hospital as HospitalModel

CMS_PHYSICIAN_API = "https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0"
CACHE_KEY = "physician_state_counts"
CACHE_TTL = 86400  # 24 hours


async def get_physician_counts_by_state() -> dict:
    """Fetches physician counts per state from CMS API with Redis caching."""
    cached = await get_cache(CACHE_KEY)
    if cached:
        return cached

    counts = {}
    limit = 5000
    offset = 0
    total = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            response = await client.get(
                CMS_PHYSICIAN_API,
                params={
                    "limit": limit,
                    "offset": offset,
                    "properties[]": ["npi", "state"],
                }
            )
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
    """
    Correlates physician density per state with average hospital rating.
    Returns data ready for scatter plot visualization.
    """
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
    """On-demand physician search from CMS API."""
    params = {"limit": limit, "offset": 0}
    conditions = []

    if state:
        conditions.append({
            "property": "state",
            "value": state,
            "operator": "=",
        })
    if specialty:
        conditions.append({
            "property": "pri_spec",
            "value": specialty.upper(),
            "operator": "=",
        })
    if name:
        conditions.append({
            "property": "provider_last_name",
            "value": name.upper(),
            "operator": "LIKE",
        })

    query_parts = [f"limit={limit}&offset=0"]
    for i, c in enumerate(conditions):
        query_parts.append(
            f"conditions[{i}][property]={c['property']}"
            f"&conditions[{i}][value]={c['value']}"
            f"&conditions[{i}][operator]={c['operator']}"
        )

    url = f"{CMS_PHYSICIAN_API}?{'&'.join(query_parts)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
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