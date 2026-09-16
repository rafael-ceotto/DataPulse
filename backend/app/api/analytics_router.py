from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import get_current_user
from app.core.duckdb_analytics import get_rating_trend, get_rating_changes, get_hospital_appearances, query_historical


router = APIRouter()

@router.get("/api/v1/analytics/rating-trend")
async def rating_trend():
    """Avg rating per pipeline run over time"""
    try:
        return get_rating_trend()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/api/v1/analytics/rating-changes")
async def rating_changes():
    """Avg rating per pipeline run over time"""
    try:
        return get_rating_changes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/api/v1/analytics/hospital-appearances")
async def hospital_appearances():
    """Hospitals that appeared or disappered across runs"""
    try:
        return get_hospital_appearances()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/v1/analytics/query")
async def custom_query(body: dict, current_user: str = Depends(get_current_user)):
    sql = body.get("sql", "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query is required")
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    try:
        return query_historical(sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
