# DataPulse

A data pipeline and REST API for CMS hospital quality data. Ingests, validates, transforms, and exposes hospital performance metrics from the Centers for Medicare & Medicaid Services (CMS).

## Stack
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, httpx
- **AI:** Groq API (openai/gpt-oss-120b) with multi-turn tool calling and web search via Tavily
- **Caching:** Redis
- **Testing:** pytest, pytest-asyncio
- **Infrastructure:** Docker, Docker Compose, GitHub Actions
- **Frontend:** React + Vite
- **Integrations:** Slack, Notion, GitHub

## Architecture

CMS (External API)
↓
Pipeline ← fetches and parses raw CSV data
↓
Pydantic Schema ← validates and types incoming data
↓
Service ← orchestrates ingestion flow
↓
Repository ← handles all database access
↓
PostgreSQL ← persists cleaned records
↓
FastAPI Router ← exposes HTTP endpoints


The pipeline follows **Medallion Architecture** principles:
- **Bronze:** raw CSV data fetched from CMS
- **Silver:** validated and typed data via Pydantic
- **Gold:** cleaned records stored in PostgreSQL, ready for API consumption and visualization

Every pipeline execution is logged in `pipeline_runs`, tracking status, records received, records processed, records failed, average rating, AI-generated insight, and error details if applicable.

## Environment Variables

Create a `backend/.env` file with the following variables:

```env
# Database
DB_URL=postgresql+asyncpg://datapulse:datapulse@localhost:5433/datapulse

# AI — required for AI query and insight generation
# Free at https://console.groq.com
GROQ_API_KEY=gsk_...

# Web Search — required for agent web search tool
# Free at https://tavily.com (1,000 searches/month)
TAVILY_API_KEY=tvly-...

# Slack — optional, sends alerts after each pipeline run
# Create an Incoming Webhook at https://api.slack.com/apps
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Notion — optional, saves AI insights to a Notion page
# Create an integration at https://notion.so/my-integrations
NOTION_TOKEN=ntn_...
NOTION_PAGE_ID=your-page-id-with-hyphens

# GitHub — optional, auto-commits insights to repository
# Create a Personal Access Token at https://github.com/settings/tokens
GITHUB_TOKEN=ghp_...
GITHUB_REPO=your-username/DataPulse
```

All integrations are optional — the core pipeline and AI features work without Slack, Notion, and GitHub configured.

## How to Run

### Authentication
The following endpoints require a Bearer token:
- `POST /api/v1/pipeline/run`
- `POST /api/v1/pipeline/run/infections`
- `POST /api/v1/ai/query`
- `POST /api/v1/notion/save`

Default credentials: `admin` / `datapulse2024`

**Start PostgreSQL and Redis:**
```bash
docker compose up -d
```

**Install dependencies:**
```bash
poetry install
```

**Run database migrations:**
```bash
cd backend
alembic upgrade head
```

**Start the API:**
```bash
cd backend
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Returns API status message |
| GET | `/health` | Returns API health status |
| POST | `/api/v1/pipeline/run` | Triggers CMS hospital data ingestion and logs execution results |
| POST | `/api/v1/pipeline/run/infections` | Triggers healthcare-associated infections data ingestion |
| GET | `/api/v1/pipeline/runs` | Returns pipeline execution history with status, records, duration, and AI-generated insights |
| GET | `/api/v1/hospitals` | Returns a paginated list of hospitals. Supports `page`, `limit`, `state`, `search`, and `min_rating` filters |
| GET | `/api/v1/hospitals/{facility_id}` | Returns a single hospital by facility ID |
| GET | `/api/v1/hospitals/metrics/rating-distribution` | Returns average hospital rating per state, ordered by rating |
| GET | `/api/v1/infections` | Lists healthcare-associated infection records. Supports `state`, `compared_to_national`, `page`, `limit` filters |
| GET | `/api/v1/infections/{facility_id}` | Returns all infection measures for a specific hospital |
| GET | `/api/v1/physicians` | On-demand physician search. Supports `state`, `specialty`, `name`, `limit` filters |
| GET | `/api/v1/physicians/state-analysis/{state}` | Physician-hospital correlation analysis by state |
| GET | `/api/v1/physicians/scarce-specialties/{state}` | Returns top 10 scarce medical specialties compared to national average |
| GET | `/api/v1/physicians/cache-status` | Returns status of national specialty cache in Redis |
| POST | `/api/v1/physicians/warm-cache` | Triggers background population of national specialty counts cache |
| POST | `/api/v1/ai/query` | Accepts a natural language question and returns results and explanation. Requires JWT. |
| POST | `/api/v1/notion/save` | Saves an AI insight to the configured Notion page. Requires JWT. |
| POST | `/api/v1/auth/token` | Returns a JWT access token. Credentials: `admin` / `datapulse2024` |

**Example:**

GET /api/v1/hospitals?page=1&limit=20&state=MA&min_rating=4


## Tests

```bash
# Run all tests
pytest -v

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# API tests only
pytest tests/api -v
```

## AI Layer

DataPulse includes a natural language query interface powered by the Groq API. The AI layer operates in two modes depending on question complexity:

**SQL mode** — simple, direct queries are translated into PostgreSQL SELECT statements and executed against the database.

**Agent mode** — complex analytical questions trigger a multi-turn tool calling loop. The agent selects and calls the appropriate tools, collects results, and synthesizes a structured response.

**Available tools:**
- `search_hospitals` — searches hospitals by state
- `get_top_rated_hospitals` — returns highest or lowest rated hospitals nationwide or by state
- `get_rating_distribution` — returns average hospital rating per state
- `get_physician_state_analysis` — returns physician and hospital metrics by state
- `get_scarce_specialties` — returns top 10 scarce specialties for a state
- `get_hospital_infections` — returns HAI infection summary for a state
- `web_search` — searches the web for external context via Tavily

**How it works:**

1. User submits a natural language question
2. Language is auto-detected — response is returned in the same language
3. If simple → LLM generates a PostgreSQL SELECT query, executes it, and explains the results
4. If complex → Agent loop runs up to 3 iterations of tool calls, then synthesizes a final response
5. Results and explanation are returned to the frontend

**Features:**
- Multilingual — auto-detects question language and responds accordingly
- Web search — combines internal database data with real-time web context
- SELECT-only enforcement — no data modification is possible
- Redis cache — responses cached for 10 minutes per question (MD5 hash key)
- Rate limited — 5 requests per minute per IP
- Save to Notion — any AI response can be saved directly to a Notion page

**Model:** openai/gpt-oss-120b via Groq API

**Example — simple query:**
```json
POST /api/v1/ai/query
{
    "question": "Which hospitals in Ohio have a 5-star rating?"
}
```

**Example — agent query with web search:**
```json
POST /api/v1/ai/query
{
    "question": "Why do hospitals in Utah have higher ratings than the national average?"
}
```

**Example — infection data query:**
```json
POST /api/v1/ai/query
{
    "question": "What is the infection rate in Ohio?"
}
```

## Automated Insight Generation

After each pipeline run, DataPulse automatically generates a natural language insight about the data using the Groq API. The insight is context-aware — it considers the last 5 historical insights to reason about trends over time.

**How it works:**

1. Pipeline completes and saves `avg_rating`
2. System fetches the previous `avg_rating` and last 5 historical insights
3. Groq receives current data + historical context
4. Groq generates a 2-3 sentence insight about trends and quality shifts
5. Insight is saved to `pipeline_runs` and displayed in the dashboard
6. Slack alert is sent with the insight
7. Insight is committed to `insights.md` in the GitHub repository

**Example insight:**
> "The average hospital rating held steady at 3.21 for this run, matching the previous cycle and indicating no measurable shift in overall quality performance. Since the metric has remained flat across consecutive periods, there is no immediate signal to adjust quality initiatives, but continued monitoring is advisable to catch any emerging trends."

**Why this matters:** The system acts proactively — it doesn't wait for a user to ask a question. Each insight influences the next, creating a reasoning chain over time. This is context-aware AI applied to a real monitoring problem, not a chatbot.

**Model:** openai/gpt-oss-120b via Groq API

## Scheduled Pipeline

DataPulse runs the data pipeline automatically using APScheduler, without requiring external infrastructure like Celery or Kubernetes CronJobs. The scheduler runs inside the FastAPI process and starts automatically when the server boots.

**Default interval:** every 6 hours (configurable)

**What runs automatically:**
- CMS hospital data ingestion (5,419 facilities)
- Healthcare-associated infections ingestion (96,055 records)
- avg_rating calculation and persistence
- AI insight generation
- Slack alert
- GitHub commit to `insights.md`

**Why APScheduler instead of Celery/Prefect:**
At this scale, an in-process scheduler is simpler, cheaper, and requires no additional infrastructure. Celery would add a broker (Redis/RabbitMQ) and worker processes. Prefect would add a cloud dependency. APScheduler runs in the same process as FastAPI with zero overhead — the right tool for the right scale.

## Integrations

### Slack
After each pipeline run, DataPulse sends an alert to a configured Slack channel with the avg_rating, variation from the previous run, and the AI-generated insight. Requires `SLACK_WEBHOOK_URL` in `.env`.

### Notion
AI query responses can be saved directly to a Notion page with a single click. The page receives the question, tools used, and full explanation as structured Notion blocks. Requires `NOTION_TOKEN` and `NOTION_PAGE_ID` in `.env`.

### GitHub
After each pipeline run, the AI-generated insight is automatically committed to `insights.md` in the repository. This creates a living document of data quality trends over time. Requires `GITHUB_TOKEN` and `GITHUB_REPO` in `.env`.

### CI Status Badge
The frontend header displays the live status of the latest GitHub Actions run, polling every 60 seconds. No configuration required — uses the public GitHub API.

## Scarce Specialty Analysis

Identifies medical specialties with significantly fewer physicians than the national average for a given state. Uses statistical sampling (50,000 records) to estimate national counts, then compares each state's share against the expected 1/56 (~1.79%).

**Scarcity ratio < 0.5** means the state has less than 50% of the expected share — a critical gap.

**Fields returned:**
- `specialty` — specialty name
- `state_count` — physicians in the state
- `national_count` — estimated national total
- `state_share_pct` — state's actual share
- `expected_share_pct` — expected share (1.79%)
- `scarcity_ratio` — actual/expected ratio
- `gap` — estimated additional physicians needed

**Cache:** national specialty data is cached for 24 hours. Call `POST /api/v1/physicians/warm-cache` to populate. On server startup, cache warming starts automatically in background.

## Technical Decisions

**Infection data in hospital cards**
When a hospital card is expanded, the UI fetches and displays a summary of healthcare-associated infections (HAI) from the `hospital_infections` table — showing counts of measures rated worse, better, or average compared to the national benchmark.

**Agent tool routing**
For known query patterns (e.g. "5-star hospitals", "lowest rated facilities"), the agent forces the correct tool on the first iteration instead of relying on the model to choose — eliminating clarification loops and improving response consistency.

**Language detection**
The agent uses `langdetect` to detect the language of each question and appends a `[LANGUAGE]` tag to the prompt, ensuring responses are always in the user's language regardless of the data language.

**Web search integration**
The agent calls Tavily's web search API as a tool when questions require context beyond the database (e.g. "why", "reason", "explain"). Internal database data is combined with real-time web results for richer responses.

**Statistical sampling for specialty analysis**
Instead of fetching all 3.3M physician records nationally, we sample 50,000 records and extrapolate using a scale factor. This reduces API calls from ~2,200 to ~33 while maintaining statistical significance.

**JWT Authentication**
POST endpoints are protected with JWT Bearer tokens. Only authenticated users can trigger pipeline runs or query the AI layer. Authentication uses `python-jose` for token generation and `bcrypt` for password hashing.

To authenticate via Swagger:
1. Call `POST /api/v1/auth/token` with `username: admin` and `password: datapulse2024`
2. Copy the `access_token` from the response
3. Click "Authorize" in Swagger and paste the token

**Redis Caching**
Frequently accessed and computationally expensive endpoints are cached in Redis:
- `GET /api/v1/hospitals/metrics/rating-distribution` — cached for 1 hour
- `POST /api/v1/ai/query` — cached per question for 10 minutes (MD5 hash key)
- `GET /api/v1/physicians/state-analysis/{state}` — cached per state for 1 hour
- Cache is invalidated automatically when the pipeline runs

**Rate Limiting**
The AI query endpoint is limited to 5 requests per minute per IP using `slowapi`. This prevents abuse of the Groq API and controls external API costs.

**Async Python**
All HTTP and database operations are async. This avoids blocking the API while waiting for external responses or I/O operations, keeping the server responsive under load.

**Repository and Service layers**
Responsibilities are clearly separated:
- **Router** receives HTTP requests and delegates to services
- **Service** coordinates business logic and orchestration
- **Repository** owns all database access

This separation makes the codebase easier to test and allows implementation changes without cascading effects across layers.

**Upsert strategy**
CMS data is re-ingested periodically. Using `INSERT ... ON CONFLICT DO UPDATE` prevents duplicate records when the same `facility_id` is encountered, keeping the dataset current without manual cleanup.

**Pipeline run logging**
Every execution is recorded from start to finish. Each run tracks status (`running`, `success`, `failed`), record counts, average rating, AI-generated insight, and error messages if applicable — making it easy to monitor data freshness and diagnose failures.

**PostgreSQL**
Open source, OLTP-optimized, and well-supported by SQLAlchemy with async drivers. A natural fit for structured healthcare data with relational integrity requirements.

## Future Improvements

- Add data quality check with Great Expectations
- Spark pipeline for large-scale batch processing of physician data
- Elasticsearch for advanced full-text search
- RAG layer for document-based queries (CMS policy documents)
- Export selected hospital cards as CSV
- Export all hospitals by state without pagination