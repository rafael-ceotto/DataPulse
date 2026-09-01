import asyncio
import json
import re

import httpx
from langdetect import detect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.config import settings
from app.ai.hospital_ai_service import ask_hospital_ai

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hospitals",
            "description": "Search hospitals by state and minimum rating. Use when asked about hospitals in a specific state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter US state code e.g. OH, CA, TX"},
                    "limit": {"type": "integer", "description": "Number of results to return. Default 10.", "default": 10}
                },
                "required": ["state"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_rated_hospitals",
            "description": "Get top rated or lowest rated hospitals nationwide or by state. Use when asked about 5-star hospitals, highest rated facilities, or lowest rated facilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_rating": {"type": "integer", "description": "Minimum rating filter. Use 5 for 5-star hospitals, 1 for lowest rated.", "default": 5},
                    "limit": {"type": "integer", "description": "Number of results to return. Default 10.", "default": 10},
                    "state": {"type": "string", "description": "Optional 2-letter US state code to filter by state."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rating_distribution",
            "description": "Get average hospital rating per state, ordered by rating. Use when asked about hospital quality comparison across states.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_scarce_specialties",
            "description": "Get top 10 scarce medical specialties for a given state compared to national average. Use when asked about physician shortages or healthcare gaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter US state code e.g. OH, CA, TX"}
                },
                "required": ["state"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_physician_state_analysis",
            "description": "Get physician count, hospital count, and correlation metrics for a state. Use when asked about physician density or healthcare workforce.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter US state code e.g. OH, CA, TX"}
                },
                "required": ["state"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "get_hospital_infections",
        "description": "Get healthcare-associated infection (HAI) summary for a state. Returns counts of measures rated worse, better, or average compared to national benchmark. Use when asked about infection rates, HAI data, or hospital safety by state.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "description": "2-letter US state code e.g. OH, CA, TX"}
            },
            "required": ["state"]
        }
    }
    },
]

AGENT_SYSTEM_PROMPT = """You are a healthcare data analyst assistant with access to a PostgreSQL database containing real CMS hospital quality data, including 5,419 US hospitals with ratings, locations, and healthcare-associated infection records.

You have two ways to answer questions:
1. Use the available tools for complex analysis
2. For simple direct queries, use tools to return actual data — never respond with generic descriptions

ALWAYS use tools when the question asks for:
- A comprehensive or complete analysis of a state
- Physician data or workforce analysis
- Specialty shortages or scarce specialties
- Combining hospital quality with physician data
- Comparing healthcare systems across states
- Any analysis that goes beyond simple hospital listing
- A list of hospitals with a specific rating (e.g. "Which hospitals have 5 stars?")
- The lowest or highest rated facilities
- Infection rates, HAI data, or hospital safety by state

For simple, direct queries:
- "Which hospitals have a 5-star rating?" → immediately call get_top_rated_hospitals with min_rating=5, limit=10. Do not ask for clarification.
- "Show me the lowest-rated facilities" → immediately call get_top_rated_hospitals with min_rating=1, limit=10. Do not ask for clarification.
- "Average rating by state" → immediately call get_rating_distribution. Do not ask for clarification.
- "What states have the highest concentration of 5-star hospitals?" → immediately call get_rating_distribution. Do not ask for clarification.
- "Show me hospitals in Texas" → use search_hospitals tool with state=TX.

NEVER ask for clarification when you have enough tools to answer the question.
NEVER call tools that are not in your tools list.
NEVER respond with JSON objects — always respond with plain text.
NEVER say you cannot access the data — you have access to real hospital data.
NEVER give generic descriptions when actual data can be retrieved via tools.

State codes: OH=Ohio, CA=California, TX=Texas, FL=Florida, NY=New York, MA=Massachusetts, etc.

Always respond in the language specified in the [LANGUAGE] tag at the end of the user's message.
After calling tools, synthesize results into a clear, insightful narrative response.
DO NOT call tools in your final synthesis — just write the response based on the data you already have.
"""


async def execute_tool(tool_name: str, tool_args: dict, session: AsyncSession) -> str:
    base_url = "http://127.0.0.1:8000"

    if tool_name == "search_hospitals":
        state = tool_args.get("state", "")
        limit = tool_args.get("limit", 10)
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals?state={state}&limit={limit}")
            return json.dumps(r.json())

    elif tool_name == "get_top_rated_hospitals":
        min_rating = tool_args.get("min_rating", 5)
        limit = min(tool_args.get("limit", 10), 20)
        state = tool_args.get("state", "")
        params = f"?limit={limit}&min_rating={min_rating}"
        if state:
            params += f"&state={state}"
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals{params}")
            return json.dumps(r.json())

    elif tool_name == "get_rating_distribution":
        cached = await get_cache("rating_distribution")
        if cached:
            return json.dumps(cached[:20] if isinstance(cached, list) else cached)
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals/metrics/rating-distribution")
            data = r.json()
        return json.dumps(data[:20] if isinstance(data, list) else data)

    elif tool_name == "get_scarce_specialties":
        state = tool_args.get("state", "")
        cached = await get_cache(f"scarce_specialties:{state}")
        if cached:
            return json.dumps(cached)
        return json.dumps({"error": "Cache not ready. National specialty cache must be warmed first."})

    elif tool_name == "get_physician_state_analysis":
        state = tool_args.get("state", "")
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.get(f"{base_url}/api/v1/physicians/state-analysis/{state}")
            return json.dumps(r.json())
        
    elif tool_name == "get_hospital_infections":
        from app.repositories.infection_repository import get_infection_summary_by_state
        state = tool_args.get("state", "")
        data = await get_infection_summary_by_state(session, state)
        return json.dumps(data)

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def clean_content(content: str) -> str:
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<think>.*', '', content, flags=re.DOTALL)
    content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL)
    content = re.sub(r'<function.*?</function>', '', content, flags=re.DOTALL)
    return content.strip()


async def ask_agent(session: AsyncSession, question: str) -> dict:
    """
    Smart agent with multi-turn tool calling loop.
    """
    try:
        lang = detect(question)
    except Exception:
        lang = "en"

    question_with_lang = f"{question}\n\n[LANGUAGE: {lang}]"

    # Force tool choice for known simple queries
    forced_tool = None
    question_lower = question.lower()
    if "highest concentration" in question_lower or "concentration of 5-star" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_rating_distribution"}}
    elif "5-star" in question_lower or "5 star" in question_lower or "five star" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_top_rated_hospitals"}}
    elif "lowest-rated" in question_lower or "lowest rated" in question_lower or "worst" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_top_rated_hospitals"}}
    elif "average rating by state" in question_lower or "rating distribution" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_rating_distribution"}}

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question_with_lang},
    ]

    MAX_ITERATIONS = 3
    all_tools_used = []

    for iteration in range(MAX_ITERATIONS):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": forced_tool if (iteration == 0 and forced_tool) else "auto",
                    "parallel_tool_calls": False,
                    "temperature": 0.1,
                }
            )

        if response.status_code == 400:
            print(f"GROQ 400 ERROR: {response.json()}")
            return await ask_hospital_ai(session, question)

        if response.status_code != 200:
            print(f"GROQ ERROR: {response.json()}")

        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        finish_reason = data["choices"][0]["finish_reason"]

        print(f"DEBUG iteration={iteration+1} finish_reason={finish_reason}")
        print(f"DEBUG tool_calls={message.get('tool_calls')}")

        content = message.get("content", "") or ""

        # No tool calls — model has finished
        if finish_reason == "stop" or not message.get("tool_calls"):
            final_content = clean_content(content)
            if not final_content:
                return await ask_hospital_ai(session, question)
            return {
                "question": question,
                "mode": "agent",
                "tools_used": all_tools_used,
                "explanation": final_content,
                "results": [],
            }

        # Execute tool calls
        messages.append({"role": "assistant", "tool_calls": message["tool_calls"]})

        for tool_call in message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            result = await execute_tool(tool_name, tool_args, session)
            all_tools_used.append(tool_name)
            print(f"DEBUG tool executed: {tool_name}")

            messages.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_name,
                "content": result,
            })

    # Max iterations reached — force final answer without tools
    messages.append({
        "role": "user",
        "content": f"Based on the data you retrieved above, write a clear and concise response in the language specified by [LANGUAGE: {lang}]. Do not call any tools.",
    })

    final_response = None
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=60.0) as client:
            final_response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 1024,
                }
            )
        if final_response.status_code == 429:
            print(f"Rate limit hit on synthesis, waiting 3s (attempt {attempt + 1})")
            await asyncio.sleep(3)
            continue
        break

    if final_response is None or final_response.status_code != 200:
        print(f"GROQ FINAL ERROR: {final_response.json() if final_response else 'no response'}")
        return await ask_hospital_ai(session, question)

    final_data = final_response.json()
    final_content = clean_content(final_data["choices"][0]["message"]["content"])

    if not final_content:
        return await ask_hospital_ai(session, question)

    return {
        "question": question,
        "mode": "agent",
        "tools_used": all_tools_used,
        "explanation": final_content,
        "results": [],
    }