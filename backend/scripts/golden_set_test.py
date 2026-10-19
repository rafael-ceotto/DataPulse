"""
Golden-set regression test for the AI agent (app/ai/hospital_agent_service.py).

Why this exists: every time we touch TOOLS or build_agent_system_prompt()
(e.g. to shorten descriptions and save tokens), there's a real risk of
silently breaking a behavior that took several rounds of live testing to get
right (see claude/DataPulse_Pending_Items.md, "AI Agent" section — the
Ohio/Vermont comparison bug alone took 6 rounds to fully fix). This script
is cheap insurance against that: it re-runs a handful of representative
real questions and checks that the agent still reaches the right MODE and
calls the right TOOLS, so a prompt-editing session can see regressions in
seconds instead of a manual re-test.

Run from inside the api container (needs GROQ_API_KEY, DB, Redis):
    docker compose exec api python scripts/golden_set_test.py

This does NOT check the quality/correctness of the generated prose — only
the mechanical parts (mode, tools_used) that are cheap to assert on and are
exactly what broke historically. Read the printed "explanation" for each
case yourself if you want a prose sanity check too.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from app.ai.hospital_agent_service import ask_agent

# Cases -> description, question, country, expected_mode, required_tools
# Req tools -> name in list must be in tools_used (order doesn't matter) -> other tools can appear too(get_rating_distribution 
# + per-state tools in comparison)
CASES = [
    (
        "Comparison (the Ohio/Vermont regression case — 6 rounds of fixes)",
        "Compare Ohio healthcare system and Vermont healthcare system, tell me about the infections rating and what CMS tell us about these two systems.",
        "US",
        "agent",
        ["get_hospital_infections", "get_hospital_infections", "search_cms_documents"],
    ),
    (
        "Simple 5-star query",
        "Which hospitals have a 5-star rating?",
        "US",
        "agent",
        ["get_top_rated_hospitals"],
    ),
    (
        "Near-me query",
        "What's the closest hospital near me?",
        "US",
        "agent",
        ["find_nearby_hospitals"],
    ),
    (
        "Hospital search by name",
        "Tell me about Miami Valley Hospital in Dayton, Ohio",
        "US",
        "agent",
        ["search_hospitals"],
    ),
    (
        "Web search (Tavily) — proves the agent goes beyond the DB",
        "What's the latest news on hospital staffing shortages in the US in 2026?",
        "US",
        "agent",
        ["web_search"],
    ),
    (
        "CMS methodology question",
        "How is the hospital star rating calculated?",
        "US",
        "agent",
        ["search_cms_documents"],
    ),
    (
        "Non-US country, Portuguese",
        "Me fale sobre o Hospital São Camilo",
        "BR",
        "agent",
        ["search_hospitals"],
    ),
    (
        "Cross-country refusal (session=BR, question names US)",
        "What are the best hospitals in the United States?",
        "BR",
        "agent",
        [],  # should NOT call hospital tools for the US while scoped to BR
    ),
]

async def main():
    failures = []
    async with AsyncSessionLocal() as session:
        for description, question, country, expected_mode, required_tools in CASES:
            print(f"\n=== {description} ===")
            print(f"Q ({country}): {question}")
            
            try:
                result = await ask_agent(session, question, country=country)
            except Exception as e:
                print(f"  ERROR: {e}")
                failures.append((description, f"raised {e!r}"))
                continue
            
            mode = result.get("mode")
            tools_used = result.get("tools_used", [])
            print(f"  mode={mode} tools_used={tools_used}")
            print(f"  explanation (first 200 chars): {result.get('explanation', '')[:200]!r}")
            
            if mode != expected_mode:
                                failures.append((description, f"expected mode={expected_mode!r}, got {mode!r}"))
            
            missing = [t for t in required_tools if t not in tools_used]
            from collections import Counter
            required_counts = Counter(required_tools)
            actual_counts = Counter(tools_used)
            for tool, count in required_counts.items():
                if actual_counts.get(tool, 0) < count:
                    failures.append((description, f"expected '{tool}' called >= {count}x, got {actual_counts.get(tool, 0)}x", ))
    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED: {len(failures)} issue(s)")
        for desc, msg in failures:
            print(f"  - [{desc}] {msg}")
        sys.exit(1)
    else:
        print(f"PASSED: all {len(CASES)} cases behaved as expected.")
        
if __name__ == "__main__":
    asyncio.run(main())