import os
from datetime import datetime, timezone

from app.core.cache import get_cache, set_cache
from app.core.logging import logger

COST_PER_1M_INPUT = 0.90
COST_PER_1M_OUTPUT = 0.90

STATS_TTL = 86400 * 30

# Daily per-user cost cap (guardrail — see claude/DataPulse_Pending_Items.md,
# "Guardrails de LLM"). Default $1.00/day/user; override via env if needed.
DAILY_COST_LIMIT_USD = float(os.getenv("DAILY_COST_LIMIT_USD", "1.00"))
# Slightly over 24h so a key created right at midnight UTC doesn't expire
# a few seconds before the day actually rolls over.
DAILY_TTL = 90000

def estimate_cost(prompt_tokens: int, completion_token: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * COST_PER_1M_INPUT
    output_cost = (prompt_tokens / 1_000_000) * COST_PER_1M_OUTPUT
    return float(f"{input_cost + output_cost:.8f}")

def _today_key(username: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"daily_cost:{username}:{today}"

async def get_daily_cost(username: str) -> float:
    value = await get_cache(_today_key(username))
    return float(value) if value is not None else 0.0

async def check_daily_limit(username: str) -> tuple[bool, float]:
    """Returns (allowed, current_spend_usd). allowed=False means the user's
    estimated spend for today (UTC) has already reached DAILY_COST_LIMIT_USD."""
    spend = await get_daily_cost(username)
    return spend < DAILY_COST_LIMIT_USD, spend

async def record_query_cost(username: str, prompt_tokens: int, completion_tokens: int):
    key = f"user_stats:{username}"
    stats =  await get_cache(key) or {
        "username": username,
        "total_queries": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_cost_usd": 0.0,
    }
    
    cost = estimate_cost(prompt_tokens, completion_tokens)
    stats["total_queries"] +=1
    stats["total_prompt_tokens"] += prompt_tokens
    stats["total_completion_tokens"] += completion_tokens
    stats["total_cost_usd"] = float(f"{stats['total_cost_usd'] + cost:.8f}")
    
    await set_cache(key, stats, ttl=STATS_TTL)

    daily_key = _today_key(username)
    new_daily_total = await get_daily_cost(username) + cost
    await set_cache(daily_key, new_daily_total, ttl=DAILY_TTL)

    logger.info("cost_tracked", username=username, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost_usd=cost, daily_total_usd=new_daily_total)
    
async def get_user_stats(username:str) -> dict:
    key = f"user_stats:{username}"
    stats = await get_cache(key)
    if not stats:
        return {
            "username": username,
            "total_queries": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost_usd": 0.0,
        }
    return stats