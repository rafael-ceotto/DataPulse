import json
import re

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.config import settings
from app.ai.hospital_ai_service import ask_hospital_ai

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_SYNTHESIS_MODEL = "qwen/qwen3.6-27b"

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
]

AGENT_SYSTEM_PROMPT = """You are a healthcare data analyst assistant with access to specialized tools.

ALWAYS use tools when the question asks for:
- A comprehensive or complete analysis of a state
- Physician data or workforce analysis
- Specialty shortages or scarce specialties
- Combining hospital quality with physician data
- Comparing healthcare systems across states
- Any analysis that goes beyond simple hospital listing

Only respond with {"use_sql": true} when the question is a simple, direct query like:
- "Which hospitals have 5 stars?"
- "Show me hospitals in Texas"
- "What is the average rating?"

For EVERYTHING else, use the available tools.

State codes: OH=Ohio, CA=California, TX=Texas, FL=Florida, NY=New York, MA=Massachusetts, etc.

Always respond in the same language as the user's question.
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

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def clean_content(content: str) -> str:
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL)
    content = re.sub(r'<function.*?</function>', '', content, flags=re.DOTALL)
    return content.strip()


async def ask_agent(session: AsyncSession, question: str) -> dict:
    """
    Smart agent with multi-turn tool calling loop.
    """
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    MAX_ITERATIONS = 5
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
                    "tool_choice": "auto",
                    "parallel_tool_calls": False,
                    "temperature": 0.1,
                }
            )
        if response.status_code != 200:
            print(f"GROQ ERROR: {response.json()}")
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        finish_reason = data["choices"][0]["finish_reason"]

        print(f"DEBUG iteration={iteration+1} finish_reason={finish_reason}")
        print(f"DEBUG tool_calls={message.get('tool_calls')}")

        # Check if model wants SQL
        content = message.get("content", "") or ""
        if "use_sql" in content:
            try:
                parsed = json.loads(content)
                if parsed.get("use_sql"):
                    return await ask_hospital_ai(session, question)
            except json.JSONDecodeError:
                pass

        # No tool calls — model has finished
        if finish_reason == "stop" or not message.get("tool_calls"):
            final_content = clean_content(content)
            if not final_content:
                # Fallback to SQL if agent returned nothing
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

    # Max iterations reached — force synthesis with different model
    async with httpx.AsyncClient(timeout=60.0) as client:
        final_response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_SYNTHESIS_MODEL,
                "messages": messages,
                "temperature": 0.1,
            }
        )
    if final_response.status_code != 200:
        print(f"GROQ FINAL ERROR: {final_response.json()}")
    final_response.raise_for_status()
    final_data = final_response.json()
    final_content = clean_content(final_data["choices"][0]["message"]["content"])

    return {
        "question": question,
        "mode": "agent",
        "tools_used": all_tools_used,
        "explanation": final_content,
        "results": [],
    }