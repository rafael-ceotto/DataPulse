"""
Quick standalone check for the daily cost guardrail (app/core/cost_tracker.py).

Why this exists: golden_set_test.py calls ask_agent() directly, bypassing
app/workers/agent_worker.py::process_message() — which is where the daily
cost check actually lives. This script tests the cost_tracker logic itself
(record_query_cost / check_daily_limit) without needing the full SQS/worker
pipeline, so it's fast and has no side effects on job_store/SQS/Realtime.

Run from inside the api container (needs Redis):
    docker compose exec api python scripts/test_cost_limit.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.cache import redis_client
from app.core.cost_tracker import (
    check_daily_limit,
    record_query_cost,
    DAILY_COST_LIMIT_USD,
    _today_key,
)

TEST_USER = "_cost_limit_test_user"


async def main():
    # start clean
    await redis_client.delete(_today_key(TEST_USER))
    await redis_client.delete(f"user_stats:{TEST_USER}")

    allowed, spend = await check_daily_limit(TEST_USER)
    print(f"Before any queries: allowed={allowed} spend=${spend:.4f} (limit=${DAILY_COST_LIMIT_USD:.2f})")
    assert allowed, "expected allowed=True with zero spend"

    # Simulate enough queries to blow past the daily limit.
    # ~24k prompt tokens + ~500 completion tokens ≈ the real Ohio/Vermont cost (~$0.044).
    queries = 0
    while True:
        await record_query_cost(TEST_USER, prompt_tokens=24000, completion_tokens=500)
        queries += 1
        allowed, spend = await check_daily_limit(TEST_USER)
        print(f"  after query {queries}: spend=${spend:.4f} allowed={allowed}")
        if not allowed or queries > 50:
            break

    if not allowed:
        print(f"\nPASSED: limit correctly reached after {queries} simulated queries (spend=${spend:.4f} >= ${DAILY_COST_LIMIT_USD:.2f}).")
    else:
        print(f"\nFAILED: limit was never reached after {queries} queries (spend=${spend:.4f}).")
        sys.exit(1)

    # cleanup
    await redis_client.delete(_today_key(TEST_USER))
    await redis_client.delete(f"user_stats:{TEST_USER}")


if __name__ == "__main__":
    asyncio.run(main())