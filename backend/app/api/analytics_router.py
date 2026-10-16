from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import get_current_user
from app.core.duckdb_analytics import get_rating_trend, get_rating_changes, get_hospital_appearances, query_historical
from app.core.logging import logger


router = APIRouter()

_GENERIC_500 = "Internal server error while running the analytics query."


@router.get("/api/v1/analytics/rating-trend")
async def rating_trend():
    """Avg rating per pipeline run over time"""
    try:
        return get_rating_trend()
    except Exception as e:
        logger.error("analytics_rating_trend_failed", error=str(e))
        raise HTTPException(status_code=500, detail=_GENERIC_500)

@router.get("/api/v1/analytics/rating-changes")
async def rating_changes():
    """Avg rating per pipeline run over time"""
    try:
        return get_rating_changes()
    except Exception as e:
        logger.error("analytics_rating_changes_failed", error=str(e))
        raise HTTPException(status_code=500, detail=_GENERIC_500)

@router.get("/api/v1/analytics/hospital-appearances")
async def hospital_appearances():
    """Hospitals that appeared or disappered across runs"""
    try:
        return get_hospital_appearances()
    except Exception as e:
        logger.error("analytics_hospital_appearances_failed", error=str(e))
        raise HTTPException(status_code=500, detail=_GENERIC_500)

@router.post("/api/v1/analytics/query")
async def custom_query(body: dict, current_user: str = Depends(get_current_user)):
    sql = body.get("sql", "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query is required")
    try:
        return query_historical(sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("analytics_custom_query_failed", error=str(e), username=current_user)
        raise HTTPException(status_code=500, detail=_GENERIC_500)