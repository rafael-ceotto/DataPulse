# DataPulse

A colleague of mine lost her parents in the same week. Both went to hospitals that didn't have what they needed.

My grandmother went through something similar. When she broke her leg, the ambulance was about to take her to the nearest hospital. Not the most appropriate one, and definitely not the one that accepted her insurance. We were lucky enough to choose differently. Most people aren't.

That's why I built DataPulse.

Hospital quality data is public. 18,595 hospitals across 10 countries. Quality ratings, infection records, physician shortages by state. Everything you need to make an informed decision about where to get treated is sitting there, underused. DataPulse makes it actually usable.

---

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, Pydantic V2, httpx
- **AI:** Groq API (openai/gpt-oss-120b) with tool calling, web search via Tavily, and RAG over CMS documents
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2) running locally
- **Messaging:** SQS via Floci — async AI query processing with job polling
- **Data:** dbt (staging, intermediate, marts), Apache Airflow, APScheduler
- **Storage:** Redis, Floci (local AWS S3 emulator) via boto3
- **Analytics:** DuckDB (historical queries over S3 pipeline snapshots)
- **Observability:** Prometheus, Grafana, Loki, structlog
- **Realtime:** Supabase Realtime (WebSocket events for AI queries and pipeline runs)
- **Infra:** Docker, Docker Compose, GitHub Actions CI/CD
- **Frontend:** React + Vite — light sidebar + dark content layout, geolocation, multi-language support (EN, PT, FR, ES, IT)
- **Integrations:** Slack, Notion, GitHub
- **Geolocation:** ZIP code geocoding via US Census lookup (33,792 ZIP codes) + Haversine proximity search
- **Big Data:** PySpark 3.5 — full 3.3M physician records processed as temporary Docker container, output saved as Parquet to S3

---

## Coverage — 10 Countries, 18,595 Hospitals

| Country | Code | Hospitals | Source |
|---------|------|-----------|--------|
| United States | US | 5,419 | CMS (Centers for Medicare & Medicaid Services) |
| Brasil | BR | 7,680 | DATASUS / Ministério da Saúde |
| United Kingdom | GB | 247 | NHS ODS |
| France | FR | 3,360 | FINESS / Ministère de la Santé |
| Belgium | BE | 111 | Wikidata / SPF Santé publique |
| Canada | CA | 432 | Wikidata / CIHI |
| Portugal | PT | 131 | Wikidata / SNS |
| España | ES | 861 | Wikidata / SNS España |
| Italia | IT | 343 | Wikidata / SSN |
| Malta | MT | 11 | Wikidata / Malta Health |
| **Total** | | **18,595** | |

---

## Architecture

```mermaid
graph TB
    subgraph Sources["Data Sources"]
        CMS[CMS API — US]
        DATASUS[DATASUS — BR]
        NHS[NHS ODS — GB]
        FINESS[FINESS — FR]
        WIKIDATA[Wikidata SPARQL — BE/CA/PT/ES/IT/MT]
    end

    subgraph Frontend["Frontend (React + Vite)"]
        UI[Dashboard]
        AIQ[Ask Doc]
        CSV[Export CSV]
        NOTION_BTN[Save to Notion]
    end

    subgraph Backend["Backend (FastAPI)"]
        Router[API Router]
        Agent[AI Agent]
        Worker[SQS Worker]
        Pipeline[Pipeline Service]
        Scheduler[APScheduler]
        Auth[JWT Auth]
    end

    subgraph Messaging["Messaging (Floci SQS)"]
        Queue[datapulse-ai-queries]
    end

    subgraph Orchestration["Orchestration (Airflow)"]
        DAG[datapulse_pipeline DAG]
        T1[ingest_hospitals]
        T2[ingest_infections]
        T3[dbt_run]
    end

    subgraph Transform["Transformation (dbt)"]
        STG[Staging Models]
        INT[Intermediate Models]
        MRT[Mart Models]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL + pgvector)]
        Redis[(Redis Cache + Jobs)]
        S3[(Floci S3\nData Lake)]
    end

    subgraph AI["AI & Search"]
        Groq[Groq API]
        Tavily[Tavily Web Search]
        Embeddings[sentence-transformers]
        DuckDB[DuckDB Analytics]
    end

    subgraph Integrations["Integrations"]
        Slack[Slack]
        NotionAPI[Notion]
        GitHub[GitHub]
        GHActions[GitHub Actions CI/CD]
    end

    Sources -->|CSV / JSON / SPARQL| Pipeline
    Pipeline --> S3
    Pipeline --> PG

    AIQ -->|POST job_id| Router
    Router --> Queue
    Queue --> Worker
    Worker --> Groq
    Worker --> Tavily
    Worker --> PG
    Worker --> DuckDB
    Worker --> Redis
    AIQ -->|GET polling| Router

    UI -->|HTTP| Router
    NOTION_BTN -->|HTTP + JWT| Router

    Router --> Pipeline
    Router --> Auth
    Router --> PG
    Router --> Redis

    DAG --> T1 --> T2 --> T3
    T3 -->|runs| STG --> INT --> MRT

    Pipeline --> Groq
    Pipeline --> Slack
    Pipeline --> NotionAPI
    Pipeline --> GitHub

    Scheduler -->|every 6h| Pipeline
    MRT --> PG
    S3 -->|DuckDB reads| DuckDB
    UI -->|polling 60s| GHActions
```

The pipeline follows **Medallion Architecture** principles — Bronze (raw source data), Silver (validated via Pydantic), Gold (PostgreSQL + dbt), Data Lake (S3 snapshots per run).

---

## How to run

```bash
# 1. Start the stack
docker compose up -d

# 2. Upload CMS PDFs to S3 and index for RAG (first time only)
cd backend
poetry run python scripts/upload_cms_docs_to_s3.py
poetry run python scripts/ingest_cms_docs.py

# 3. Run country processors (first time only)
docker compose --profile belgium run --rm belgium_processor
docker compose --profile canada run --rm canada_processor
docker compose --profile portugal run --rm portugal_processor
docker compose --profile spain run --rm spain_processor
docker compose --profile italy run --rm italy_processor
docker compose --profile malta run --rm malta_processor

# 4. Ingest all countries via API
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=datapulse2024" | jq -r .access_token)

curl -s -X POST http://localhost:8000/api/v1/pipeline/run/belgium -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/v1/pipeline/run/canada -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/v1/pipeline/run/portugal -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/v1/pipeline/run/spain -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/v1/pipeline/run/italy -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/api/v1/pipeline/run/malta -H "Authorization: Bearer $TOKEN"
```

Frontend at `http://localhost` · API at `http://localhost:8000` · Docs at `http://localhost:8000/docs`

To verify S3 data lake contents:

```bash
docker run --rm --network datapulse_default \
  -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli s3 ls s3://datapulse --recursive --endpoint-url http://floci:4566
```

**Optional:**
```bash
# Airflow (first run needs airflow_init)
docker compose --profile airflow up airflow_init
docker compose --profile airflow up airflow_webserver airflow_scheduler -d

# dbt manually
docker compose --profile dbt run --rm dbt
```

**Authentication:** `POST /api/v1/auth/token` with `username=admin` / `password=datapulse2024`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/token` | Returns a JWT |
| POST | `🔒 /api/v1/pipeline/run` | Triggers US hospital data ingestion |
| POST | `🔒 /api/v1/pipeline/run/belgium` | Triggers Belgium ingestion |
| POST | `🔒 /api/v1/pipeline/run/canada` | Triggers Canada ingestion |
| POST | `🔒 /api/v1/pipeline/run/portugal` | Triggers Portugal ingestion |
| POST | `🔒 /api/v1/pipeline/run/spain` | Triggers Spain ingestion |
| POST | `🔒 /api/v1/pipeline/run/italy` | Triggers Italy ingestion |
| POST | `🔒 /api/v1/pipeline/run/malta` | Triggers Malta ingestion |
| POST | `🔒 /api/v1/pipeline/run/infections` | Triggers infection data ingestion |
| GET | `🔒 /api/v1/pipeline/runs` | Execution history with AI-generated insights |
| GET | `/api/v1/hospitals` | Paginated list. Supports `page`, `limit`, `state`, `city`, `search`, `min_rating`, `max_rating`, `country` |
| GET | `🔒 /api/v1/hospitals/export` | All hospitals by state or city. Supports `state`, `city`, `country` |
| GET | `🔒 /api/v1/hospitals/data-quality` | Completeness, unrated, low-rated metrics per country |
| GET | `/api/v1/hospitals/{facility_id}` | Hospital by ID |
| GET | `/api/v1/hospitals/metrics/rating-distribution` | Average rating by state |
| GET | `/api/v1/hospitals/nearby` | Hospitals within radius. Supports `lat`, `lng`, `radius`, `country`, `min_rating` |
| GET | `/api/v1/hospitals/stats/count` | Total hospital count across all countries |
| GET | `/api/v1/hospitals/stats/country` | Stats per country (total, emergency, phone, coords, types) |
| GET | `/api/v1/ai/country-summary` | AI-generated healthcare system summary per country (cached 24h) |
| GET | `/api/v1/infections` | Infection records. Supports `state`, `compared_to_national` |
| GET | `/api/v1/infections/{facility_id}` | Infections for a facility |
| GET | `/api/v1/physicians` | Physician search. Supports `state`, `specialty`, `name` |
| GET | `/api/v1/physicians/state-analysis/{state}` | Physician-hospital correlation by state |
| GET | `/api/v1/physicians/scarce-specialties/{state}` | Top 10 scarce specialties vs national average |
| POST | `🔒 /api/v1/ai/query` | Submit AI query — returns `job_id` |
| GET | `🔒 /api/v1/ai/query/{job_id}` | Poll for AI query result |
| GET | `🔒 /api/v1/ai/stats` | Token usage and cost per user |
| POST | `🔒 /api/v1/notion/save` | Save insight to Notion |
| GET | `/api/v1/analytics/rating-trend` | Avg rating per pipeline run |
| GET | `/api/v1/analytics/rating-changes` | States with most change across runs |
| GET | `/api/v1/analytics/hospital-appearances` | Hospitals missing from some runs |
| POST | `🔒 /api/v1/analytics/query` | Custom DuckDB SQL query over S3 snapshots |

---

## Environment Variables

Create `backend/.env`:

```env
DB_URL=postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse
GROQ_API_KEY=gsk_...          # required — free at console.groq.com
TAVILY_API_KEY=tvly-...       # required — free at tavily.com
SLACK_WEBHOOK_URL=...         # optional
NOTION_TOKEN=...              # optional
NOTION_PAGE_ID=...            # optional
GITHUB_TOKEN=...              # optional
GITHUB_REPO=your-username/DataPulse
PIPELINE_INTERVAL_HOURS=6
AI_RATE_LIMIT_PER_MINUTE=5
SUPABASE_URL=https://...      # required for Realtime
SUPABASE_ANON_KEY=eyJ...      # required for Realtime
```

---

## The AI layer

The agent operates in two modes. **SQL mode** for direct questions where "Which hospitals have 5 stars in Ohio?" becomes a SELECT and returns data. **Agent mode** for complex analysis. It pulls data from the database, searches the web, reads CMS documents, and synthesizes a response.

AI queries are processed asynchronously via SQS. The endpoint returns a `job_id` immediately, and the frontend receives the result instantly via Supabase Realtime WebSocket. Cached queries return synchronously with zero latency and zero cost.

The country summary endpoint generates a 3–4 sentence overview of each country's healthcare system in the country's primary language (Italian for IT, Portuguese for BR and PT, French for FR and BE, Spanish for ES, English for US/CA/GB/MT). Results are cached in Redis for 24 hours.

**Available tools:** `search_hospitals`, `get_top_rated_hospitals`, `get_rating_distribution`, `get_physician_state_analysis`, `get_scarce_specialties`, `get_hospital_infections`, `web_search`, `search_cms_documents`, `get_historical_analytics`

The agent is multilingual. It detects the language of the question and responds in the same language (EN, PT, ES, FR, IT, DE).

Each response shows token usage and estimated cost. User-level stats available at `GET /api/v1/ai/stats`.

The agent supports **conversational memory**. Each conversation has a unique ID and the agent remembers context across queries for 24 hours. Users can start a new conversation at any time via the "↺ New conversation" button.

---

## Example queries

- "Compare the healthcare system from Ohio and Vermont"
- "What are the CMS criteria for a hospital to receive a 5-star rating?"
- "What scarce specialties does California have?"
- "Compare South Dakota and Utah infection rates"
- "How has the average hospital rating changed across pipeline runs?"
- "Which hospitals near me have emergency services?"
- "Quais hospitais têm 5 estrelas em Ohio?"
- "¿Por qué el CMS cambió la metodología de calificación de estrellas en 2026?"
- "Warum hat das CMS die Stern-Bewertungsmethodik im Jahr 2026 geändert?"

---

## Key technical decisions

**Wikidata SPARQL for 7 of 10 countries** — most countries don't have structured, open hospital APIs. Wikidata covers them all with a consistent SPARQL query — only the country QID changes (Q38 for Italy, Q233 for Malta, etc.). This allowed scaling from 2 to 10 countries in one week.

**City filter instead of state filter for Wikidata countries** — Wikidata countries store a fixed country name in the `state` column (e.g. "Italia"). The `CITY_FILTER_COUNTRIES` set in the repository layer switches the filter to `city ILIKE '%value%'` for BE, CA, IT, MT, PT, ES, GB, FR — keeping the API interface consistent across all countries.

**SQS for async AI queries** — queries go into a Floci SQS queue. A worker processes them without blocking the API. Cached queries bypass the queue entirely.

**pgvector instead of a dedicated vector database** — DataPulse already uses PostgreSQL. No new infrastructure for 447 chunks.

**DuckDB over S3 snapshots** — every pipeline run exports a JSON snapshot. DuckDB reads them directly for historical queries that PostgreSQL can't answer, because the database only keeps the current state.

**sentence-transformers locally** — zero cost, zero latency, no external dependency at query time. The model is downloaded once at Docker build time.

**Floci instead of LocalStack** — LocalStack Community was sunset in March 2026. Floci is the MIT-licensed replacement: no account, no token, ~90MB, starts in ~24ms. Moving to real AWS S3 is a one-line change.

**freeipapi.com for IP geolocation** — used in the onboarding modal to detect the user's country. Replaced ipapi.co which blocked requests from localhost due to CORS policy. Falls back to US if the detected country is not in the supported list.

**flagcdn.com for flag images** — emoji flags don't render on Windows. flagcdn.com provides flag images at fixed sizes (20×15, 40×30, 80×60). Used in the header, sidebar, hero, and onboarding modal.

**PySpark for full physician dataset** — the scarce specialties analysis previously sampled 50,000 records from 3.3M. PySpark now processes the full dataset as a temporary container, saves results as Parquet to S3 partitioned by state, and DuckDB reads them in milliseconds.

**JWT-based rate limiting** — each authenticated user has an independent 5/min limit, regardless of IP. Multi-tenant ready.

**Upsert instead of delete+insert** — the pipeline can run as many times as needed without duplicates.

**Conversational memory per session** — each conversation is stored in Redis under `conversation:{username}:{conversation_id}` with a 24h TTL.

**Proactive anomaly detection** — after every pipeline run, the system automatically checks for rating drops, completeness issues, and unusual counts of low-rated hospitals. Alerts go to Slack independently of the insight generation.

**Structured output validation** — every agent response is validated against a Pydantic schema before being returned.

**Supabase Realtime instead of polling** — AI query results are delivered via WebSocket. When the SQS worker finishes processing, it publishes an `ai_query_done` event to Supabase.

**ZIP code geocoding instead of a geocoding API** — hospital coordinates are derived from ZIP codes using a public US Census lookup table with 33,792 entries. Zero cost, zero external dependency, works offline.

---

## Testing

```bash
cd backend
poetry run pytest tests/ -v           # all tests
poetry run pytest tests/evaluation -v # agent evaluation suite
```

The evaluation suite runs in CI with `continue-on-error: true` — it reports agent behavior without blocking the pipeline.

---

## Development

Common commands during development:

```bash
# Rebuild after backend changes
docker compose build api && docker compose up -d api

# Rebuild after frontend changes
docker compose build frontend && docker compose up -d frontend

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL

# Clear only AI query cache
docker compose exec redis redis-cli KEYS "ai_query*"
docker compose exec redis redis-cli DEL "ai_query:<hash>"

# Clear country summary cache
docker compose exec redis redis-cli DEL "country_summary:IT"

# View API logs
docker compose logs api --tail=30

# Run pipeline directly
cd backend
poetry run python run_pipeline.py

# Run PySpark physician processing job
docker compose --profile spark build physician_processor
docker compose --profile spark run --rm physician_processor

# Re-upload CMS PDFs and re-index after Floci restart
cd backend
poetry run python scripts/upload_cms_docs_to_s3.py
poetry run python scripts/ingest_cms_docs.py
```

---

## What's next

- **Voice integration** — wake word detection ("Hey Doc", "Oi Doc", "Ciao Doc") via Web Speech API. On activation, the agent receives the spoken question with geolocation context and responds in the country's language via Speech Synthesis API. Emergency detection triggers a direct call button to the nearest hospital.
- **Native app** — Expo + React Native for App Store and Google Play. The FastAPI backend stays unchanged. Voice via expo-speech and expo-av (more robust than Web Speech API on mobile).
- **Data enrichment** — hospitals from Wikidata countries (BE, CA, IT, MT, PT, ES, GB) are missing phone numbers, addresses, and zip codes. OpenStreetMap Overpass API and country-specific open data portals are the next sources to explore.
- **Insurance/plans per hospital** — add accepted insurance plans. US: CMS payer data. BR: ANS (Agência Nacional de Saúde Suplementar) open data.