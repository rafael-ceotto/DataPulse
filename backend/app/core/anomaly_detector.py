from app.core.logging import logger

async def detect_anomalies(current_avg: float, previous_avg: float | None, quality: dict) -> list[str]:
    #Checking for anomalies in pipeline run and returns a list of anomaly descriptions
    anomalies = []
    #Rating drop
    if previous_avg is not None:
        variation = round(current_avg - previous_avg, 3)
        if variation <= -0.05:
            anomalies.append(f"⚠️ Average rating dropped by {abs(variation)} points compared to previous run ({previous_avg} → {current_avg}).")
        elif variation >= 0.05:
            anomalies.append(f"✅ Average rating improved by {variation} points compared to previous run ({previous_avg} → {current_avg}).")
    #Completeness drop
    completeness = quality.get("completeness_pct", 100)
    if completeness < 55:
        anomalies.append(
            f"🔴 Data completeness dropped to {completeness}% — below the 55% threshold. "
            f"{quality.get('unrated_hospitals', 0):,} hospitals have no rating."
        )
    elif completeness < 60:
        anomalies.append(
            f"🟡 Data completeness at {completeness}% — approaching the warning threshold."
        )
    #Low rated hospitals
    low_rated = quality.get("low_rated_hospitals", 0)
    if low_rated > 700:
        anomalies.append(f"🔴 {low_rated:,} hospitals rated 1 or 2 stars — unusually high count.")
    if not anomalies:
        anomalies.append("✅ No anomalies detected. Data quality and ratings are within normal range.")
        
    logger.info("anomly_detection_complete", anomaly_count=len(anomalies))
    return anomalies
        