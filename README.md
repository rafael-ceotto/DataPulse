# DataPulse

A colleague of mine lost her parents in the same week. Both went to hospitals that didn't have what they needed.

My grandmother went through something similar. When she broke her leg, the ambulance was about to take her to the nearest hospital. Not the most appropriate one, and definitely not the one that accepted her insurance. By that time, we were lucky enough to have means to transport her with a private ambulance instead of the public one and send her to the chosen hospital.

It's been a while and trust me when I say that still haunts me.

That's why I built DataPulse.

The idea is straightforward: CMS (Centers for Medicare & Medicaid Services) data is public, and it has everything you need to make an informed decision about where to get treated. DataPulse takes that data, processes it, validates it, and exposes it in a way anyone can use: whether you're a patient looking for the best hospital for a rare cancer, or a health administrator analyzing the quality of an entire network.

Think about it this way: if you have a rare cancer and there's a specialized oncology hospital in Arizona, why would you settle for a generic one closer to home? With DataPulse, you have that information before you need it.

---

## What it does

DataPulse ingests, validates, and transforms data from 5,419 hospitals and 96,055 hospital infection records from CMS. All of that feeds an API that exposes quality metrics, physician analysis by state, scarce specialties, and a search interface that works both with direct SQL queries and an AI agent that knows when to go beyond internal data. This includes official CMS policy documents.

The part I'm most proud of isn't the most obvious one. It's not the pipeline, and it's not the agent. It's the scarce specialty analysis. Knowing that a state has less than 50% of the specialists it should have is the kind of information that can save a life. If someone opens DataPulse and uses that before choosing where to get treated, the project was worth it.

---

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL + pgvector, Pydantic, httpx
- **AI:** Groq API (openai/gpt-oss-120b) with tool calling, web search via Tavily, and RAG over CMS documents
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2) running locally
- **Data Transformation:** dbt (staging, intermediate, marts)
- **Orchestration:** Apache Airflow
- **Caching:** Redis
- **Storage:** Floci (local AWS S3 emulator) via boto3
- **Testing:** pytest, pytest-asyncio
- **Infrastructure:** Docker, Docker Compose, GitHub Actions
- **Frontend:** React + Vite
- **Integrations:** Slack, Notion, GitHub
- **Observability:** Prometheus, Grafana, Loki, structlog

---

## Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (React + Vite)"]
        UI[Dashboard]
        AIQ[AI Query]
        CSV[Export CSV]
        NOTION_BTN[Save to Notion]
    end

    subgraph Backend["Backend (FastAPI)"]
        Router[API Router]
        Agent[AI Agent]
        Pipeline[Pipeline Service]
        Scheduler[APScheduler]
        Auth[JWT Auth]
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
        Redis[(Redis Cache)]
        S3[(Floci S3\nData Lake)]
    end

    subgraph ExternalData["External Data Sources"]
        CMS[CMS API]
        Physicians[CMS Physicians API]
        CMSPDF[CMS PDF Documents]
    end

    subgraph AI["AI & Search"]
        Groq[Groq API\nopenai/gpt-oss-120b]
        Tavily[Tavily\nWeb Search]
        Embeddings[sentence-transformers\nall-MiniLM-L6-v2]
    end

    subgraph Integrations["Integrations"]
        Slack[Slack\nAlerts]
        NotionAPI[Notion\nInsights Page]
        GitHub[GitHub\ninsights.md]
        GHActions[GitHub Actions\nCI/CD]
    end

    UI -->|HTTP| Router
    AIQ -->|HTTP + JWT| Router
    NOTION_BTN -->|HTTP + JWT| Router
    CSV -->|direct| UI

    Router --> Agent
    Router --> Pipeline
    Router --> Auth

    Agent --> Groq
    Agent --> Tavily
    Agent --> PG
    Agent --> Redis

    CMSPDF -->|upload_cms_docs_to_s3.py| S3
    S3 -->|ingest_cms_docs.py| Embeddings
    Embeddings -->|vector chunks| PG
    Agent -->|search_cms_documents| PG

    DAG --> T1 --> T2 --> T3
    T1 -->|triggers| Pipeline
    T2 -->|triggers| Pipeline
    T3 -->|runs| STG --> INT --> MRT

    Pipeline --> CMS
    Pipeline --> Physicians
    Pipeline --> PG
    Pipeline --> S3
    Pipeline --> Groq
    Pipeline --> Slack
    Pipeline --> NotionAPI
    Pipeline --> GitHub

    Scheduler -->|every 6h| Pipeline
    MRT --> PG

    Router --> PG
    Router --> Redis

    UI -->|polling 60s| GHActions
```

The pipeline follows **Medallion Architecture** principles:
- **Bronze:** raw CSV data fetched directly from CMS
- **Silver:** validated and typed via Pydantic
- **Gold:** clean records in PostgreSQL, ready for consumption and dbt transformation
- **Data Lake:** processed records exported to S3 after each pipeline run

---

## Environment Variables

Create a `backend/.env` file:

```env
# Database
DB_URL=postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse

# Groq — required for AI query and insight generation
# Free at https://console.groq.com
GROQ_API_KEY=gsk_...

# Tavily — required for web search in the agent
# Free at https://tavily.com (1,000 searches/month)
TAVILY_API_KEY=tvly-...

# Slack — optional, sends alerts after each pipeline run
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Notion — optional, saves AI insights to a Notion page
NOTION_TOKEN=ntn_...
NOTION_PAGE_ID=your-page-id-with-hyphens

# GitHub — optional, auto-commits insights to the repository
GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-username/DataPulse

# Scheduler interval in hours (default: 6)
PIPELINE_INTERVAL_HOURS=6

# AI rate limit per minute (default: 5)
AI_RATE_LIMIT_PER_MINUTE=5
```

All integrations are optional. The pipeline and AI work without them.

---

## How to run

### With Docker (recommended)

```bash
# 1. Start main stack (db, redis, api, frontend, floci, prometheus, loki, grafana)
docker compose up -d

# 2. Upload CMS PDFs to S3 (first time only)
cd backend
poetry run python scripts/upload_cms_docs_to_s3.py

# 3. Index CMS documents for RAG (first time only)
poetry run python scripts/ingest_cms_docs.py

> **Note:** After the stack is up, the pipeline can also be triggered directly from the **Pipeline Runs** section in the frontend UI via the "▶ Run Pipeline" button.

# 4. Optional — start Airflow (webserver + scheduler)
# Note: airflow_init only needed on first run
docker compose --profile airflow up airflow_init
docker compose --profile airflow up airflow_webserver airflow_scheduler -d

# 5. Optional — run dbt manually
docker compose --profile dbt run --rm dbt

# To stop everything
docker compose --profile airflow down
docker compose down
```

> **Note:** Airflow uses `profiles: [airflow]` and does **not** start with `docker compose up -d`. It must be started explicitly with `--profile airflow`. Same for dbt.

The frontend is available at `http://localhost` and the API at `http://localhost:8000`.

To rebuild only what changed:

```bash
docker compose build api && docker compose up -d api            # backend changes
docker compose build frontend && docker compose up -d frontend  # frontend changes
```

### With Airflow

To start the full orchestration stack:

```bash
# Initialize Airflow (first time only)
docker compose --profile airflow up airflow_init

# Start Airflow webserver and scheduler
docker compose --profile airflow up airflow_webserver airflow_scheduler -d
```

Airflow UI available at `http://localhost:8080`. Credentials: `admin` / `datapulse2024`.

### With dbt only

To run dbt models manually:

```bash
docker compose --profile dbt run --rm dbt
```

Or locally:

```bash
cd backend/datapulse
dbt run
dbt test
dbt docs serve  # documentation at http://localhost:8080
```

### Locally

```bash
# Start only the database, Redis, and Floci
docker compose up db redis floci floci_init -d

# Install dependencies
poetry install

# Run migrations
cd backend
alembic upgrade head

# Upload CMS PDFs to S3
poetry run python scripts/upload_cms_docs_to_s3.py

# Index CMS documents for RAG
poetry run python scripts/ingest_cms_docs.py

# Start the API
uvicorn app.main:app --reload

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

API docs at `http://localhost:8000/docs`.

### Authentication

The following endpoints require a Bearer token:

POST /api/v1/auth/token
username: admin
password: datapulse2024


Protected endpoints:
- `POST /api/v1/pipeline/run`
- `POST /api/v1/pipeline/run/infections`
- `GET /api/v1/pipeline/runs`
- `GET /api/v1/hospitals/export`
- `GET /api/v1/hospitals/data-quality`
- `POST /api/v1/ai/query`
- `POST /api/v1/notion/save`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Health check |
| POST | `🔒 /api/v1/pipeline/run` | Triggers hospital data ingestion |
| POST | `🔒 /api/v1/pipeline/run/infections` | Triggers infection data ingestion |
| GET | `🔒 /api/v1/pipeline/runs` | Execution history with AI-generated insights |
| GET | `/api/v1/hospitals` | Paginated hospital list. Supports `page`, `limit`, `state`, `search`, `min_rating` |
| GET | `🔒 /api/v1/hospitals/export` | All hospitals in a state without pagination. Requires `state` |
| GET | `🔒 /api/v1/hospitals/data-quality` | Data quality metrics: completeness, unrated, low-rated |
| GET | `/api/v1/hospitals/{facility_id}` | Hospital by facility ID |
| GET | `/api/v1/hospitals/metrics/rating-distribution` | Average rating by state |
| GET | `/api/v1/infections` | Infection records. Supports `state`, `compared_to_national`, `page`, `limit` |
| GET | `/api/v1/infections/{facility_id}` | Infections for a specific facility |
| GET | `/api/v1/physicians` | Physician search. Supports `state`, `specialty`, `name`, `limit` |
| GET | `/api/v1/physicians/state-analysis/{state}` | Physician-hospital correlation by state |
| GET | `/api/v1/physicians/scarce-specialties/{state}` | Top 10 scarce specialties vs national average |
| GET | `/api/v1/physicians/cache-status` | Specialty cache status |
| POST | `/api/v1/physicians/warm-cache` | Populates specialty cache in background. Called automatically on first scarce specialties request |
| POST | `🔒 /api/v1/ai/query` | Natural language query. Requires JWT |
| POST | `🔒 /api/v1/notion/save` | Saves an insight to Notion. Requires JWT |
| POST | `/api/v1/auth/token` | Returns a JWT |

---

## Testing

```bash
pytest -v                    # all tests
pytest tests/unit -v         # unit tests
pytest tests/integration -v  # integration tests
pytest tests/api -v          # API tests
```

**Coverage includes:**
- Pipeline ingestion (hospital and infection)
- Repository layer (hospital, infection, pipeline runs)
- Service layer (hospital_service, infection_service, insight_service)
- Integration layer (slack, notion, github)
- AI utilities (clean_content)
- All API endpoints with authentication

---

## The AI layer

This is the part that evolved the most during development. The agent isn't a chatbot. It's an analyst with access to real data that knows when it needs to look beyond the database and when it needs to look beyond the web too. It can also dive into the actual policy documents behind the data.

It operates in two modes:

**SQL mode** — for direct questions. "Which hospitals have 5 stars in Ohio?" becomes a SELECT query and returns the data.

**Agent mode** — for complex analysis. "Why do hospitals in Utah have higher ratings than the national average?" triggers a tool calling loop: it pulls the rating distribution from the database, then goes to the web for external context, and synthesizes everything into a coherent response.

What I find most interesting is that the agent decides on its own which mode to use and, when it needs web search or document retrieval, it uses them. It's not a static system; it's one that knows when internal data isn't enough.

**Available tools:**
- `search_hospitals` — hospitals by state
- `get_top_rated_hospitals` — highest or lowest rated
- `get_rating_distribution` — average rating by state
- `get_physician_state_analysis` — physicians and hospitals by state
- `get_scarce_specialties` — scarce specialties
- `get_hospital_infections` — HAI infection summary by state
- `web_search` — external search via Tavily
- `search_cms_documents` — semantic search over official CMS methodology PDFs with source and page citation

Any response can be saved to Notion with one click.

---

## Example queries

The agent is multilingual. It detects the language of the question and responds in the same language. A few examples of what you can ask:

**In English:**
- "Compare the healthcare system from Ohio and Vermont"
- "What are the CMS criteria for a hospital to receive a 5-star rating?"
- "Which states have the highest concentration of 5-star hospitals?"
- "What scarce specialties does California have compared to the national average?"
- "Show me the lowest-rated hospitals in Florida"
- "How is the overall star rating calculated?"
- "What states have the worst infection rates?"
- "Why did CMS change the star rating methodology in 2026?"

**Em português:**
- "Quais hospitais têm 5 estrelas em Ohio?"
- "Compare o sistema de saúde do Texas com o da Califórnia"
- "Quais especialidades médicas estão em falta em Nova York?"
- "Como é calculada a nota dos hospitais pelo CMS?"
- "Qual é o número mínimo de grupos de medidas que um hospital precisa para receber uma classificação de estrelas?"

**En español:**
- "¿Qué hospitales tienen 5 estrellas en Texas?"
- "¿Cuáles son los estados con mejor calidad hospitalaria?"
- "Compara el sistema de salud de Florida y Nueva York"
- "¿Qué especialidades médicas escasean en California?"
- "¿Por qué el CMS cambió la metodología de calificación de estrellas en 2026?"

**En français:**
- "Pourquoi le CMS a-t-il modifié la méthodologie de notation par étoiles en 2026?"
- "Quel est le nombre minimum de groupes de mesures qu'un hôpital doit avoir pour recevoir une évaluation en étoiles?"

**In italiano:**
- "Perché il CMS ha cambiato la metodologia di valutazione a stelle nel 2026?"

**Auf Deutsch:**
- "Warum hat das CMS die Stern-Bewertungsmethodik im Jahr 2026 geändert?"

Questions about CMS methodology (like "How is the star rating calculated?") are answered directly from the official CMS documents, with the source and page number cited in the response.

---

## RAG over CMS documents

The agent can answer questions about CMS policy, star rating methodology, and regulatory requirements. Not from its training data, but from the actual official documents.

Two PDFs are indexed: the Comprehensive Methodology Report v3.0 (2018) and v5.1 (2026), totalling 447 chunks. When the agent calls `search_cms_documents`, it generates an embedding for the question using `all-MiniLM-L6-v2`, runs a cosine similarity search via pgvector, and retrieves the most relevant chunks. Each with its source document and page number.

The reason for using pgvector instead of a dedicated vector database is simple: DataPulse already uses PostgreSQL. Enabling the extension requires no new infrastructure, no new service, and no new operational concept. The vector store lives in the same database as the hospital data.

The CMS PDFs live in S3. To upload them and index them:

```bash
cd backend
poetry run python scripts/upload_cms_docs_to_s3.py  # upload to S3
poetry run python scripts/ingest_cms_docs.py         # download from S3, chunk, embed, store
```

To add more CMS documents, drop PDFs into `cms_docs/`, upload them, and run the ingestion script again. It deletes and re-indexes each file on every run, so re-ingestion is safe.

---

## S3 data lake

After every pipeline run, the processed hospital records are automatically exported to S3 as `pipeline-runs/{run_id}/hospitals.json`. This creates a versioned, append-only history of every dataset the pipeline has ever produced: a lightweight data lake pattern without any additional infrastructure.

The CMS methodology PDFs are also stored in S3 under `cms-docs/`. The ingestion script downloads them from there, processes them locally, and cleans up. The source of truth for the documents is S3, not the local filesystem.

DataPulse uses **Floci** as the local S3 emulator — a free, open-source drop-in replacement for LocalStack Community, which was sunset in March 2026. Floci starts in ~24ms, weighs ~90MB, requires no account or auth token, and is 100% compatible with the AWS S3 SDK. Swapping to real AWS S3 in production requires only changing the endpoint URL and credentials.

The S3 bucket structure:

s3://datapulse/
pipeline-runs/
{run_id}/
hospitals.json
cms-docs/
Comprehensive Methodology Report (v3.0) (01-05-18).pdf
Comprehensive Methodology Report (v5.1) (04-28-2026).pdf


---

## Automatic insights

After every pipeline run, the system automatically generates an insight about the data using Groq. What makes this different from a simple summary is that the agent considers the last 5 previous insights before generating the next one so it reasons about trends, not just the current moment.

After generating, the insight goes to three places: the database (shows up in the Pipeline Runs dashboard), Slack (as an alert), and the repository (as a commit to `insights.md`).

---

## dbt transformation layer

After ingestion, dbt transforms the raw data into analytical models organized in three layers:

**Staging** — 1:1 with source tables, light cleaning only:
- `stg_hospitals` — cleaned hospital records
- `stg_infections` — infections with benchmark category derived
- `stg_pipeline_runs` — successful pipeline runs with duration

**Intermediate** — joins and business logic:
- `int_hospital_quality` — hospitals joined with their infection summary
- `int_state_metrics` — state-level aggregations including completeness

**Marts** — final models ready for consumption:
- `mart_hospital_quality` — hospitals with rating categories and infection percentages
- `mart_state_health_summary` — state health overview with latest pipeline context
- `mart_data_quality` — data quality metrics for monitoring

dbt runs automatically after each pipeline ingestion. To run manually:

```bash
cd backend/datapulse
dbt run    # build all models
dbt test   # run data tests
dbt docs serve  # browse documentation and lineage graph
```

---

## Airflow orchestration

The full pipeline is orchestrated by Apache Airflow with a DAG that runs every 6 hours:

ingest_hospitals → ingest_infections → dbt_run
PythonOperator PythonOperator BashOperator


Each task calls the DataPulse API endpoints with JWT authentication, maintaining a clear separation between the orchestrator and the application. The DAG includes retry logic (1 retry with 5-minute delay) and is pausable from the Airflow UI.

Start the Airflow stack:

```bash
docker compose --profile airflow up airflow_webserver airflow_scheduler -d
```

UI at `http://localhost:8080` — credentials: `admin` / `datapulse2024`.

---

## Scheduled pipeline

The scheduler runs the full pipeline every 6 hours without any manual intervention. The interval is configurable via `PIPELINE_INTERVAL_HOURS` in `.env`.

---

## Integrations

**Slack** — alert after each pipeline run with the average rating, variation from the previous run, and the generated insight. Also sends a data quality alert when completeness drops below 55%.

**Notion** — any AI Query response can be saved to a Notion page with one click. It saves the question, tools used, and full explanation as structured blocks.

**GitHub** — insights are automatically committed to `insights.md`, creating a living record of data quality trends over time.

**CI badge** — the frontend header shows the latest CI status in real time, polling every 60 seconds via the public GitHub API.

---

## Observability

DataPulse ships with a full observability stack out of the box. When you run `docker compose up`, everything starts automatically.

- **Prometheus** — scrapes metrics from the API every 15 seconds via `/metrics`. Available at `http://localhost:9090`.
- **Grafana** — pre-provisioned dashboard with four panels. Available at `http://localhost:3000`.
- **Loki** — collects structured logs from all containers via the Loki Docker driver. Available at `http://localhost:3100`.

Grafana credentials: `admin` / `datapulse2024`

**Dashboard panels:**
- **Request Rate** — requests per second across all endpoints
- **Requests by Status Code** — breakdown of 2xx, 4xx, 5xx responses
- **P95 Latency** — 95th percentile response time per endpoint
- **Error Rate** — rate of 4xx and 5xx responses (empty means zero errors)

To explore logs in Grafana, go to **Explore** → select **loki** as data source → query `{job="datapulse_api"}`.

The dashboard is provisioned automatically from `grafana/dashboards/datapulse-dashboard.json`.

---

## Data quality

The current CMS dataset has ~58.6% completeness (41.4% of hospitals don't have an overall rating). That's not a bug, it's a known limitation of the public data. DataPulse surfaces this transparently in the Data Quality dashboard, alongside alerts for low-rated hospitals and missing fields. A Slack alert fires automatically when completeness drops below 55%.

---

## Scarce specialty analysis

Identifies medical specialties with significantly fewer physicians than the national average for a given state. Uses statistical sampling (50,000 records) to estimate national counts, then compares each state's share against the expected 1/56 (~1.79%).

A scarcity ratio below 0.5 means the state has less than half the specialists it should. A critical gap.

On first load after a cold start, the cache is built automatically in the background when a scarce specialties request is made. The frontend shows a warming state and polls every 30 seconds until ready. The cache is persisted to disk via Redis RDB snapshots and survives container restarts.

---

## Technical decisions

**Why APScheduler and not Celery?** At this scale, adding a broker and separate workers would be over-engineering. The scheduler runs in the same process as the API with zero overhead.

**Why Airflow for orchestration?** Airflow adds visibility where you can see the DAG graph, retry failed tasks, and monitor run history from a UI. It also decouples orchestration from application code: the DAG calls the API endpoints rather than importing Python functions directly, which means the orchestrator and the application can evolve independently.

**Why pgvector instead of a dedicated vector database?** DataPulse already uses PostgreSQL. Enabling the pgvector extension requires no new infrastructure. The vector store lives in the same database as the hospital data. For the scale of this project, it's the right tool.

**Why sentence-transformers locally instead of an API?** Zero cost, zero latency on embedding generation, and no external dependency at query time. The model (`all-MiniLM-L6-v2`, 90MB) is downloaded once during the Docker build and cached in the image avoiding the need to download again at runtime.

**Why not classic RAG only?** The agent uses RAG for policy questions, web search for current context, and direct SQL for data questions. Each tool has its place. A system that only does RAG would be honest about documents but blind to the actual data; one that only does SQL would be precise about the data but ignorant of the rules behind it.

**Why Floci instead of LocalStack?** LocalStack Community was sunset in March 2026 and now requires an auth token, security updates are frozen, and the image is over 1GB. Floci is the MIT-licensed, no-strings-attached replacement: no account, no token, ~90MB image, starts in ~24ms. The AWS S3 SDK works unchanged, only the endpoint URL differs. Moving to real AWS S3 in production is a one-line change.

**Upsert instead of delete+insert** — CMS updates its data periodically. With `INSERT ... ON CONFLICT DO UPDATE`, the pipeline can run as many times as needed without creating duplicates.

**Sampling for specialty analysis** — instead of fetching 3.3M physician records nationally, we sample 50,000 and extrapolate. This reduces API calls from ~2,200 to ~33 while maintaining statistical significance.

**Three CSV export modes** — current page, all hospitals in a state, or only the ones the user expanded (with infection data included).

---

## What's next

- Elasticsearch for advanced full-text search