import asyncio
import json
import re
import os
import unicodedata

import httpx
from langdetect import detect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.config import settings
from app.core.logging import logger
from app.ai.hospital_ai_service import ask_hospital_ai
from app.core.output_validator import validate_agent_output

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hospitals",
            "description": "Search hospitals by state and/or by name. Use 'search' when the question names a specific hospital (e.g. 'Miami Valley Hospital', 'Hospital São Camilo') — it does a fuzzy match on the hospital name. Use 'state' when the question asks about hospitals in a specific state/region, with no specific hospital named. You can combine both.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "2-letter state/region code, e.g. OH, CA, TX (US) or SP, RJ, MG (Brazil). Optional if 'search' is provided."},
                    "search": {"type": "string", "description": "Hospital name (or part of it) to search for, e.g. 'Miami Valley Hospital' or 'São Camilo'. Use this whenever a specific hospital is named in the question."},
                    "limit": {"type": "integer", "description": "Number of results to return. Default 10.", "default": 10}
                },
                "required": []
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
                    "max_rating": {"type": "integer", "description": "Maximum rating filter. Use 1 for lowest rated hospitals."},
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
            "name": "find_nearby_hospitals",
            "description": "Find the best hospitals near a location, ranked by overall rating (closest first among equally-rated ones). Use this for 'near me', 'closest', 'nearby', 'perto de mim', 'próximo a mim', 'na minha região' questions, or any question that names a neighborhood/city/area as the search point instead of a full state. Works for any selected country. If the user's device location is already known it is used automatically — you don't need to pass lat/lng yourself. Only pass 'location_text' when a specific place is named in the question (e.g. a neighborhood, city, or landmark) and you want that place used instead of (or in addition to) the device location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_text": {"type": "string", "description": "A neighborhood, city, or place name mentioned in the question, e.g. 'Zona Norte, São Paulo' or 'Dayton, Ohio'. Omit if the question just says 'near me'/'perto de mim' with no place named."},
                    "min_rating": {"type": "integer", "description": "Optional minimum overall rating filter."},
                    "emergency_only": {"type": "boolean", "description": "Set true when the question asks specifically about emergency rooms/emergency care near the location.", "default": False},
                    "limit": {"type": "integer", "description": "Number of results to return. Default 10.", "default": 10}
                },
                "required": []
            }
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
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or context about healthcare, hospitals, or medical topics. Use when the question asks 'why', 'reason', 'explain', or requires context beyond the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query to find relevant information."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_cms_documents",
            "description": "Search official CMS policy documents, methodology guides, and star rating technical notes. Use when asked about CMS criteria, rating methodology, how star ratings are calculated, regulatory requirements, or any question about the rules and policies behind hospital quality ratings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The question or topic to search for in CMS documents."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_historical_analytics",
            "description": "Query historical data across multiple pipeline runs stored in S3. Use when asked about trends over time, how ratings changed across runs, or historical comparisons. Available analyses: 'rating_trend' (avg rating per run), 'rating_changes' (states with most change), 'hospital_appearances' (hospitals missing from some runs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis": {
                        "type": "string",
                        "description": "Type of analysis to run. One of: 'rating_trend', 'rating_changes', 'hospital_appearances'.",
                        "enum": ["rating_trend", "rating_changes", "hospital_appearances"]
                    }
                },
                "required": ["analysis"]
            }
        }
    },
]

_HOSPITAL_FIELDS_FOR_LLM = [
    "facility_name", "address", "city", "state", "overall_rating",
    "raw_rating_label", "emergency_services", "telephone_number", "distance_miles",
]

def _trim_hospitals(rows):
    if not isinstance(rows, list):
        return rows
    trimmed = []
    for row in rows:
        if not isinstance(row, dict):
            trimmed.append(row)
            continue
        trimmed.append({k: row[k] for k in _HOSPITAL_FIELDS_FOR_LLM if k in row})
    return trimmed


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()

def _location_parts(location_text: str) -> list[str]:
    # Split on commas first. If there's no comma (e.g. "Zona Norte de São Paulo",
    # a natural phrase with no punctuation), also split on common connector words
    # (Portuguese, French, Spanish, Italian) so the city name doesn't stay trapped
    # inside one opaque blob.
    raw_segments = [s.strip() for s in location_text.split(",") if s.strip()]
    if len(raw_segments) <= 1:
        raw_segments = re.split(
            r"\s+(?:de|da|do|das|dos|du|des|del|dei|degli|delle|em|na|no|nas|nos|en|à|al|in)\s+",
            location_text,
            flags=re.IGNORECASE,
        )
        raw_segments = [s.strip() for s in raw_segments if s.strip()]
    return raw_segments or [location_text.strip()]


async def geocode_location(location_text: str, country: str) -> dict | None:
    async def _query(q: str, limit: int = 10) -> list:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "limit": limit,
                    "countrycodes": country.lower(),
                    "addressdetails": 1,
                },
                headers={"User-Agent": "DataPulse/1.0"},
            )
            if r.status_code != 200 or not r.text.strip():
                return []
            return r.json()

    try:
        results = await _query(location_text, limit=10)

        # A phrase like "Zona Norte de São Paulo" is ambiguous on its own (many
        # Brazilian cities have a "Zona Norte"), and the city name can appear in
        # any position. So instead of trusting result #1, require that a candidate
        # mention EVERY distinct part of the phrase — that's what actually rules
        # out a same-named neighborhood in the wrong city (e.g. Natal's "Zona Norte").
        parts = _location_parts(location_text)
        normalized_parts = [_normalize_text(p) for p in parts]

        chosen = None
        if len(normalized_parts) > 1:
            for res in results:
                name = _normalize_text(res.get("display_name", ""))
                if all(p in name for p in normalized_parts):
                    chosen = res
                    break

        if chosen is None and len(parts) > 1:
            # No single result mentioned every part — try geocoding each part on
            # its own and keep the one whose own query had the fewest results
            # (a more specific/unique name, as opposed to a generic area name
            # that matches many unrelated places).
            best = None
            for part in parts:
                part_results = await _query(part, limit=5)
                if part_results and (best is None or len(part_results) < best[1]):
                    best = (part_results[0], len(part_results))
            if best:
                chosen = best[0]

        if chosen is None and results:
            chosen = results[0]

        if chosen is None:
            logger.warning("geocode_location_no_match", location_text=location_text)
            return None

        logger.info(
            "geocode_location_resolved",
            location_text=location_text,
            resolved_name=chosen.get("display_name"),
            lat=chosen["lat"],
            lng=chosen["lon"],
        )
        return {"lat": float(chosen["lat"]), "lng": float(chosen["lon"])}
    except Exception as e:
        logger.error("geocode_location_failed", location_text=location_text, error=str(e))
        return None


async def execute_tool(
    tool_name: str,
    tool_args: dict,
    session: AsyncSession,
    country: str = "US",
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> str:
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    if tool_name == "search_hospitals":
        state = tool_args.get("state", "")
        search = tool_args.get("search", "")
        limit = tool_args.get("limit", 10)
        params = f"?limit={limit}&country={country}"
        if state:
            params += f"&state={state}"
        if search:
            params += f"&search={search}"
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals{params}")
            return json.dumps(_trim_hospitals(r.json()))

    elif tool_name == "get_top_rated_hospitals":
        max_rating = tool_args.get("max_rating", None)
        min_rating = tool_args.get("min_rating", None if max_rating is not None else 5)
        limit = min(tool_args.get("limit", 10), 20)
        state = tool_args.get("state", "")
        params = f"?limit={limit}&country={country}"
        if min_rating is not None:
            params += f"&min_rating={min_rating}"
        if max_rating is not None:
            params += f"&max_rating={max_rating}"
        if state:
            params += f"&state={state}"
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals{params}")
            return json.dumps(_trim_hospitals(r.json()))

    elif tool_name == "get_rating_distribution":
        cache_key = f"rating_distribution:{country}"
        cached = await get_cache(cache_key)
        if cached:
            return json.dumps(cached)
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals/metrics/rating-distribution?country={country}")
            data = r.json()
        return json.dumps(data)

    elif tool_name == "find_nearby_hospitals":
        location_text = tool_args.get("location_text")
        lat = None
        lng = None

        # An explicitly named place ("perto de Copacabana") should win over the
        # device's physical location — someone in São Paulo can still ask about
        # a hospital near a place they're not standing in.
        if location_text:
            geo = await geocode_location(location_text, country)
            if geo:
                lat, lng = geo["lat"], geo["lng"]

        if lat is None or lng is None:
            lat = user_lat
            lng = user_lng

        min_rating = tool_args.get("min_rating")
        emergency_only = tool_args.get("emergency_only", False)
        limit = min(tool_args.get("limit", 10), 20)

        if lat is None or lng is None:
            # No device location and no resolvable named place — fall back to a
            # country-wide "best rated" list instead of failing outright.
            params = f"?limit={limit}&country={country}"
            if min_rating is not None:
                params += f"&min_rating={min_rating}"
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{base_url}/api/v1/hospitals{params}")
                fallback_results = r.json()
            if not isinstance(fallback_results, list):
                return json.dumps({
                    "error": "no_location",
                    "message": "No location is available. Ask the user to share their device location, or to name a specific city or neighborhood to search near.",
                })
            if emergency_only:
                fallback_results = [h for h in fallback_results if h.get("emergency_services") in ("Yes", "Sim")]
            return json.dumps({
                "no_location_fallback": True,
                "message": "No device location or named place was available — these are the top-rated hospitals countrywide, not proximity-based.",
                "results": _trim_hospitals(fallback_results[:limit]),
            })

        params = f"?lat={lat}&lng={lng}&radius=50&limit=30&country={country}"
        if min_rating is not None:
            params += f"&min_rating={min_rating}"

        async with httpx.AsyncClient() as client:
            r = await client.get(f"{base_url}/api/v1/hospitals/nearby{params}")
            results = r.json()

        if not isinstance(results, list):
            return json.dumps(results)

        if emergency_only:
            results = [h for h in results if h.get("emergency_services") in ("Yes", "Sim")]

        results.sort(key=lambda h: (-(h.get("overall_rating") or 0), h.get("distance_miles", 9999)))
        return json.dumps(_trim_hospitals(results[:limit]))

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

    elif tool_name == "web_search":
        from tavily import TavilyClient
        query = tool_args.get("query", "")
        tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = tavily.search(query, max_results=3)
        snippets = [
            f"- {r['title']}: {r['content'][:300]}"
            for r in results.get("results", [])
        ]
        return json.dumps({"results": snippets})

    elif tool_name == "search_cms_documents":
        from app.rag.retriever import search_documents
        query = tool_args.get("query", "")
        chunks = await search_documents(query, session)
        if not chunks:
            return json.dumps({"results": [], "message": "No CMS documents indexed yet. Run the ingestion script first."})
        formatted = [
            f"[Source: {c['source']}, Page {c['page']}, Similarity: {c['similarity']}]\n{c['content']}"
            for c in chunks
        ]
        return json.dumps({"results": formatted})

    elif tool_name == "get_historical_analytics":
        from app.core.duckdb_analytics import get_rating_trend, get_rating_changes, get_hospital_appearances
        analysis = tool_args.get("analysis", "rating_trend")
        if analysis == "rating_trend":
            data = get_rating_trend()
        elif analysis == "rating_changes":
            data = get_rating_changes()
        elif analysis == "hospital_appearances":
            data = get_hospital_appearances()
        else:
            data = []
        return json.dumps(data)

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def clean_content(content: str) -> str:
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<think>.*', '', content, flags=re.DOTALL)
    content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL)
    content = re.sub(r'<function.*?</function>', '', content, flags=re.DOTALL)
    return content.strip()


APOLOGY_MESSAGES = {
    "pt": "Desculpe, não consegui gerar uma resposta agora (limite de uso da IA foi atingido). Tente novamente em alguns segundos.",
    "en": "Sorry, I couldn't generate an answer right now (AI usage limit reached). Please try again in a few seconds.",
    "es": "Lo siento, no pude generar una respuesta ahora (límite de uso de la IA alcanzado). Inténtalo de nuevo en unos segundos.",
}


async def _safe_fallback(session: AsyncSession, question: str, lang: str) -> dict:
    try:
        return await ask_hospital_ai(session, question)
    except Exception as e:
        logger.error("ask_hospital_ai_fallback_failed", error=str(e))
        message = APOLOGY_MESSAGES.get(lang, APOLOGY_MESSAGES["en"])
        return validate_agent_output({
            "question": question,
            "mode": "error",
            "tools_used": [],
            "explanation": message,
            "results": [],
            "tokens_used": {"prompt": 0, "completion": 0, "total": 0},
            "estimated_cost_usd": 0,
        })


async def ask_agent(
    session: AsyncSession,
    question: str,
    username: str = "admin",
    conversation_id: str | None = None,
    country: str = "US",
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> dict:
    try:
        lang = detect(question)
    except Exception:
        lang = "en"

    question_with_lang = f"{question}\n\n[LANGUAGE: {lang}]"

    # Load conversation history BEFORE building messages
    history = []
    if conversation_id:
        from app.core.conversation_memory import get_conversation_history
        history = await get_conversation_history(username, conversation_id)

    forced_tool = None
    question_lower = question.lower()
    if any(kw in question_lower for kw in [
        "cms criteria", "star rating method", "how is the rating", "rating calculated",
        "cms methodology", "cms requirement", "criteria for",
        "como é calculada", "como funciona a nota", "critérios do cms", "metodologia do cms",
        "como é calculado", "nota dos hospitais",
        "cómo se calcula", "criterios del cms", "metodología del cms", "cómo funciona la nota",
    ]):
        forced_tool = {"type": "function", "function": {"name": "search_cms_documents"}}
    elif "5-star" in question_lower or "5 star" in question_lower or "five star" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_top_rated_hospitals"}}
    elif "lowest-rated" in question_lower or "lowest rated" in question_lower or ("worst" in question_lower and "infection" not in question_lower):
        forced_tool = {"type": "function", "function": {"name": "get_top_rated_hospitals"}}
    elif "average rating by state" in question_lower or "rating distribution" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_rating_distribution"}}
    elif "highest concentration" in question_lower or "concentration of 5-star" in question_lower:
        forced_tool = {"type": "function", "function": {"name": "get_top_rated_hospitals"}}
    elif any(kw in question_lower for kw in [
        "near me", "nearby", "close to", "closest",
        "perto de", "perto da", "perto do", "perto das", "perto dos",
        "próximo a", "próximo de", "próximo da", "próximo do",
        "proxima a", "proxima de", "proxima da", "proxima do",
        "na minha região", "na minha regiao", "nas proximidades",
        "près de moi", "proche de moi", "le plus proche",
        "cerca de mí", "cerca de mi", "más cercano", "mas cercano",
        "vicino a me", "più vicino", "piu vicino",
    ]):
        forced_tool = {"type": "function", "function": {"name": "find_nearby_hospitals"}}

    messages = [
    {"role": "system", "content": build_agent_system_prompt(country)},
    *history,
    {"role": "user", "content": question_with_lang},
    ]

    MAX_ITERATIONS = 3
    all_tools_used = []
    collected_results = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

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
            logger.error("groq_400_error", detail=str(response.json()))
            return await _safe_fallback(session, question, lang)

        if response.status_code == 429:
            logger.warning("groq_rate_limit", iteration=iteration + 1)
            await asyncio.sleep(5)
            continue

        if response.status_code != 200:
            logger.error("groq_error", detail=str(response.json()))

        response.raise_for_status()
        data = response.json()

        usage = data.get("usage", {})
        total_prompt_tokens += usage.get("prompt_tokens", 0)
        total_completion_tokens += usage.get("completion_tokens", 0)

        message = data["choices"][0]["message"]
        finish_reason = data["choices"][0]["finish_reason"]

        logger.info("groq_iteration", iteration=iteration + 1, finish_reason=finish_reason)

        content = message.get("content", "") or ""

        if finish_reason == "stop" or not message.get("tool_calls"):
            final_content = clean_content(content)
            if not final_content:
                return await _safe_fallback(session, question, lang)
            if conversation_id:
                from app.core.conversation_memory import append_to_conversation
                await append_to_conversation(username, conversation_id, question, final_content)
            from app.core.cost_tracker import estimate_cost
            cost = estimate_cost(total_prompt_tokens, total_completion_tokens)
            return validate_agent_output({
                    "question": question,
                    "mode": "agent",
                    "tools_used": all_tools_used,
                    "explanation": final_content,
                    "results": collected_results[:50],
                    "tokens_used": {
                        "prompt": total_prompt_tokens,
                        "completion": total_completion_tokens,
                        "total": total_prompt_tokens + total_completion_tokens,
                    },
                    "estimated_cost_usd": cost,
            })

        messages.append({"role": "assistant", "tool_calls": message["tool_calls"]})

        for tool_call in message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            result = await execute_tool(tool_name, tool_args, session, country, user_lat, user_lng)
            all_tools_used.append(tool_name)
            logger.info("tool_executed", tool_name=tool_name)

            if tool_name in ("search_hospitals", "get_top_rated_hospitals", "get_rating_distribution", "find_nearby_hospitals"):
                try:
                    parsed = json.loads(result)
                    rows = None
                    if isinstance(parsed, list):
                        rows = parsed
                    elif isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
                        rows = parsed["results"]
                    if rows is not None:
                        if tool_name == "find_nearby_hospitals":
                            collected_results = [
                                r for r in collected_results
                                if not (isinstance(r, dict) and "distance_miles" in r)
                            ]
                        collected_results.extend(rows)
                except (json.JSONDecodeError, TypeError):
                    pass

            messages.append({
                "tool_call_id": tool_call["id"],
                "role": "tool",
                "name": tool_name,
                "content": result,
            })

    messages.append({
        "role": "user",
        "content": f"Based on the data you retrieved above, write a clear and concise response in the language specified by [LANGUAGE: {lang}]. Do not call any tools.",
    })

    final_response = None
    for attempt in range(2):
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
            logger.warning("groq_rate_limit_synthesis", attempt=attempt + 1)
            await asyncio.sleep(3)
            continue
        break

    if final_response is None or final_response.status_code != 200:
        logger.error("groq_final_error", detail=str(final_response.json()) if final_response else "no response")
        return await _safe_fallback(session, question, lang)

    final_data = final_response.json()

    usage = final_data.get("usage", {})
    total_prompt_tokens += usage.get("prompt_tokens", 0)
    total_completion_tokens += usage.get("completion_tokens", 0)

    final_content = clean_content(final_data["choices"][0]["message"]["content"])

    if not final_content:
        return await _safe_fallback(session, question, lang)

    if conversation_id:
        from app.core.conversation_memory import append_to_conversation
        await append_to_conversation(username, conversation_id, question, final_content)

    from app.core.cost_tracker import estimate_cost
    cost = estimate_cost(total_prompt_tokens, total_completion_tokens)

    return validate_agent_output({
        "question": question,
        "mode": "agent",
        "tools_used": all_tools_used,
        "explanation": final_content,
        "results": collected_results[:50],
        "tokens_used": {
            "prompt": total_prompt_tokens,
            "completion": total_completion_tokens,
            "total": total_prompt_tokens + total_completion_tokens,
        },
        "estimated_cost_usd": cost,
    })  


COUNTRY_NAMES = {
    "US": "the United States",
    "BR": "Brazil",
    "CA": "Canada",
    "GB": "the United Kingdom",
    "FR": "France",
    "BE": "Belgium",
    "PT": "Portugal",
    "ES": "Spain",
    "IT": "Italy",
    "MT": "Malta",
}


def build_agent_system_prompt(country: str = "US") -> str:
    country_name = COUNTRY_NAMES.get(country, country)

    if country == "US":
        scope_intro = (
            "You are a healthcare data analyst assistant with access to a PostgreSQL database containing "
            "real CMS hospital quality data, including 5,419 US hospitals with ratings, locations, and "
            "healthcare-associated infection records. You also have access to official CMS policy documents "
            "and methodology guides via the search_cms_documents tool."
        )
        scope_notes = ""
    else:
        scope_intro = (
            f"You are a healthcare data analyst assistant. The user has selected {country_name} as the active "
            f"country, and your hospital tools (search_hospitals, get_top_rated_hospitals, get_rating_distribution, "
            f"find_nearby_hospitals) return real hospital data for {country_name} when called — the country filter "
            f"is already applied automatically, you don't need to specify it yourself."
        )
        scope_notes = (
            f"\nIMPORTANT: Physician workforce analysis (get_scarce_specialties, get_physician_state_analysis), "
            f"healthcare-associated infection data (get_hospital_infections), and CMS policy documents "
            f"(search_cms_documents) are US-only today and have no {country_name} equivalent yet. If asked about "
            f"those topics for {country_name}, say honestly that this specific analysis isn't available for "
            f"{country_name} yet, instead of claiming you have no hospital data at all — you DO have hospital "
            f"listings and ratings for {country_name}.\n"
        )
    state_code_note = (
            "\nState codes: OH=Ohio, CA=California, TX=Texas, FL=Florida, NY=New York, MA=Massachusetts, VT=Vermont, etc.\n"
            if country == "US" else ""
        )
    return f"""{scope_intro}

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
- Questions asking "why", "reason", "explain", or requiring context beyond the database
- Current healthcare news or policy changes
- CMS criteria, rating methodology, star rating rules, or regulatory requirements → use search_cms_documents
- Any comparison query that mentions "infection" → use get_hospital_infections for each state mentioned.
- A specific hospital is named in the question → use search_hospitals with the 'search' parameter set to that hospital's name.
- When answering about a SPECIFIC named hospital (not a list), keep any table compact: only Facility Name, City/State, Overall Rating, Emergency Services, and Phone. Do NOT include facility ID, exact address, ZIP code, or latitude/longitude in the table — mention those in plain text only if the user explicitly asks for the address or exact location.
- A question asks for the "best"/"closest" hospital or emergency room "near me"/"nearby"/"perto de mim"/"próximo a mim", or names a neighborhood/city as the search point instead of a full state → use find_nearby_hospitals. Don't pass lat/lng yourself — the device location (if available) is applied automatically. Only pass location_text when a specific place is named in the question. Works the same way for any selected country.
- "What's the best emergency room near me?" / "qual a melhor emergência perto de mim" → use find_nearby_hospitals with emergency_only=true.
- IMPORTANT: Specialty-specific rankings (e.g. "best hospital for cardiology near me") are NOT available yet — there is no medical-specialty data in the database. If asked for a specialty-specific nearby hospital, say honestly that specialty-level filtering isn't available yet, then still call find_nearby_hospitals to show the best-rated hospitals nearby in general as the closest useful answer.
- IMPORTANT: Most non-US countries in this app have no CMS-style numeric overall_rating — some (like Brazil) have no national rating at all, others (like the UK) use a non-numeric category instead, found in the raw_rating_label field (e.g. "Outstanding", "Good", "Requires Improvement") rather than overall_rating. When overall_rating is null, check raw_rating_label before concluding there's no rating — report it honestly if present ("rated Good by the CQC"), and only say no rating system exists if both are empty. Either way, always list hospitals by distance/name/address as the most useful answer — never leave the response empty.
- Whenever your answer lists hospitals (from find_nearby_hospitals or search_hospitals), always name the top/closest/most relevant hospital explicitly in your own sentence — not only inside the table. For example say "The closest option is São Luiz Rede D'Or, on Rua Figueiredo Magalhães 700, with an emergency room" instead of a generic "Here is a hospital:" followed only by a table. Do this in every language, and especially when there is no rating to anchor the sentence around.
{scope_notes}
IMPORTANT: This session is scoped to {country_name} ({country}). If the question explicitly names a different country (e.g. asks about a hospital in the United States, Brazil, France, the UK, etc. while this session is set to a different one), do NOT search or answer for that other country — instead, in the language of the user's question, tell them this session is currently set to {country_name} and that they should switch the country selector if they want data from elsewhere. Do not call any tools for that other country in this case.
For simple, direct queries:
- "Which hospitals have a 5-star rating?" → immediately call get_top_rated_hospitals with min_rating=5, limit=10. Do not ask for clarification.
- "Show me the lowest-rated facilities" → immediately call get_top_rated_hospitals with max_rating=1, limit=10. Do not ask for clarification.
- "Average rating by state" → immediately call get_rating_distribution. Do not ask for clarification.
- "What states have the highest concentration of 5-star hospitals?" → call get_top_rated_hospitals with min_rating=5, limit=20, then synthesize which states appear most frequently. Do not ask for clarification.
- "Show me hospitals in Texas" → use search_hospitals tool with state=TX.
- "Tell me about Miami Valley Hospital in Dayton, Ohio" → use search_hospitals tool with search="Miami Valley Hospital" (and state=OH if you want to narrow it further). Do NOT just list hospitals in the state — use the name search.
- "Me fale sobre o Hospital São Camilo" (Portuguese) → use search_hospitals tool with search="São Camilo". If the question mentions a Brazilian state, pass it as state too (e.g. state=SP for São Paulo).
- "What are the CMS criteria for 5-star hospitals?" → immediately call search_cms_documents. Do not ask for clarification.
- "How is the star rating calculated?" → immediately call search_cms_documents. Do not ask for clarification.
- "How has the average hospital rating changed across pipeline runs?" → immediately call get_historical_analytics with analysis='rating_trend'. Do not ask for clarification.
- "Which states changed the most between pipeline runs?" → immediately call get_historical_analytics with analysis='rating_changes'. Do not ask for clarification.
- "What's the best hospital near me?" / "qual o melhor hospital perto de mim" → immediately call find_nearby_hospitals. Do not ask for clarification.
- "Best hospital near Zona Norte, São Paulo" → call find_nearby_hospitals with location_text="Zona Norte, São Paulo".

For comparison queries in any language:
- "Compare the healthcare system from Ohio and Vermont" → call get_rating_distribution, then get_physician_state_analysis for OH, then get_physician_state_analysis for VT. Synthesize into a narrative comparison. Do NOT return a raw hospital list.
- "Compare o sistema de saude de Ohio e California" (Portuguese) → call get_rating_distribution, then get_physician_state_analysis for OH, then get_physician_state_analysis for CA. Synthesize into a narrative comparison in Portuguese. Do NOT return a raw hospital list.
- "Compara el sistema de salud de Florida y Nueva York" (Spanish) → call get_rating_distribution, then get_physician_state_analysis for FL, then get_physician_state_analysis for NY. Synthesize into a narrative comparison in Spanish. Do NOT return a raw hospital list.
- Any question containing "compare", "comparar", "comparação", "versus", "vs", "difference between", "diferença entre" → always use get_rating_distribution + get_physician_state_analysis for each state mentioned. NEVER return a raw list as the answer to a comparison question.
- "Compare South Dakota and Utah infection rates" → call get_hospital_infections for SD, then get_hospital_infections for UT. Synthesize into a narrative comparison. Do NOT return a raw list.

When using search_cms_documents results, always mention the source document and page number in your response so the user knows exactly where the information comes from.

When displaying rating distribution or any list of states, always show ALL states in the table. Never abbreviate with "…" or "etc." — every row must be visible.

NEVER ask for clarification when you have enough tools to answer the question.
NEVER call tools that are not in your tools list.
NEVER respond with JSON objects — always respond with plain text.
NEVER say you cannot access the data — you have access to real hospital data for {country_name}, and (for the United States) CMS documents too.
NEVER give generic descriptions when actual data can be retrieved via tools.
If a search_hospitals call by name returns no matching hospital, say so honestly instead of inventing a generic sentence about it.
If find_nearby_hospitals returns no_location_fallback=true, tell the user plainly that their exact location wasn't available (no device location shared and no place named), so you're showing the best-rated hospitals countrywide instead — not proximity-based. Still name the top one from that list in your sentence, the same way you would for a real nearby result.

{state_code_note}

Always respond in the language specified in the [LANGUAGE] tag at the end of the user's message.
After calling tools, synthesize results into a clear, insightful narrative response.
DO NOT call tools in your final synthesis — just write the response based on the data you already have."""