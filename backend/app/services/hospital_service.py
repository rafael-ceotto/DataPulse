from sqlalchemy.ext.asyncio import AsyncSession
import subprocess

from app.pipeline.cms_ingestion import fetch_data_cms, parse_hospitals
from app.repositories.hospital_repository import save_hospitals, get_data_quality_metrics
from app.repositories.pipeline_run_repository import create_pipeline_run, update_pipeline_run, get_previous_avg_rating, get_recent_insights
from app.ai.insight_service import generate_insight
from app.core.slack import send_slack_alert
from app.core.github import commit_insight

COMPLETENESS_THRESHOLD = 55.0


async def ingest_hospitals(session: AsyncSession):
    pipeline_run = await create_pipeline_run(session)
    try:
        csv_text = await fetch_data_cms()
        if csv_text is None:
            raise ValueError("Failed to fetch data from CMS")

        hospitals = parse_hospitals(csv_text)
        await save_hospitals(session, hospitals)

        rated = [h.overall_rating for h in hospitals if h.overall_rating is not None]
        avg_rating = round(sum(rated) / len(rated), 2) if rated else None

        # Generate Insight
        insight = None
        if avg_rating is not None:
            try:
                print(f"=== INSIGHT: generating for avg_rating={avg_rating} ===")
                previous_avg = await get_previous_avg_rating(session)
                print(f"=== INSIGHT: previous_avg={previous_avg} ===")
                history = await get_recent_insights(session, limit=5)
                print(f"=== INSIGHT: history={len(history)} items ===")
                insight = await generate_insight(avg_rating, previous_avg, history)
                print(f"=== INSIGHT: generated={insight[:50]} ===")

                # Slack alert — pipeline insight
                variation = round(avg_rating - previous_avg, 3) if previous_avg else None
                emoji = "🟡" if variation is None else ("🔴" if variation < -0.01 else ("🟢" if variation > 0.01 else "⚪"))
                slack_message = (
                    f"{emoji} *DataPulse Pipeline Alert*\n"
                    f"*Avg Rating:* {avg_rating} "
                    f"{'(' + ('+' if variation > 0 else '') + str(variation) + ' vs previous)' if variation is not None else '(first run)'}\n"
                    f"*Insight:* {insight}"
                )
                await send_slack_alert(slack_message)

                # Commit insight to GitHub
                await commit_insight(avg_rating, insight)

            except Exception as e:
                print(f"Insight generation failed: {e}")

        # Data quality alert
        try:
            quality = await get_data_quality_metrics(session)
            completeness = quality.get("completeness_pct", 100)
            if completeness < COMPLETENESS_THRESHOLD:
                await send_slack_alert(
                    f"⚠️ *DataPulse Data Quality Alert*\n"
                    f"*Completeness dropped to {completeness}%* — below the {COMPLETENESS_THRESHOLD}% threshold.\n"
                    f"*Unrated hospitals:* {quality.get('unrated_hospitals', 0):,}\n"
                    f"*Low rated (≤2★):* {quality.get('low_rated_hospitals', 0):,}"
                )
        except Exception as e:
            print(f"Data quality alert failed: {e}")

        # Run dbt models
        try:
            result = subprocess.run(
                ["dbt", "run", "--profiles-dir", "/app/datapulse", "--project-dir", "/app/datapulse"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                print("=== DBT: models refreshed successfully ===")
            else:
                print(f"=== DBT: failed — {result.stderr[:200]} ===")
        except Exception as e:
            print(f"=== DBT: error — {e} ===")

        await update_pipeline_run(
            session,
            pipeline_run,
            status="success",
            records_received=len(hospitals),
            records_processed=len(hospitals),
            records_failed=0,
            avg_rating=avg_rating,
            insight=insight,
        )
        return len(hospitals)

    except Exception as e:
        await update_pipeline_run(
            session,
            pipeline_run,
            status="failed",
            records_received=0,
            records_processed=0,
            records_failed=0,
            error_message=str(e),
        )
        raise