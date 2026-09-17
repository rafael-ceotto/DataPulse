from app.core.cache import get_cache, set_cache
from app.core.logging import logger

COST_PER_1M_INPUT = 0.90
COST_PER_1M_OUTPUT = 0.90

STATS_TTL = 86400 * 30

def estimate_cost(prompt_tokens: int, completion_token: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * COST_PER_1M_INPUT
    output_cost = (prompt_tokens / 1_000_000) * COST_PER_1M_OUTPUT
    return float(f"{input_cost + output_cost:.8f}")

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
    logger.info("cost_tracked", username=username, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost_usd=cost)
    
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