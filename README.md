# DataPulse

A data pipeline and REST API for CMS hospital quality data. Ingests, validates, transforms, and exposes hospital performance metrics from the Centers for Medicare & Medicaid Services (CMS).

## Stack
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, httpx
- **Testing:** pytest, pytest-asyncio
- **Infrastructure:** Docker, Docker Compose, GitHub Actions
- **Frontend:** React (in progress)

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

Every pipeline execution is logged in `pipeline_runs`, tracking status, records received, records processed, records failed, and error details if applicable.

## How to Run

### Authentication
The following endpoints require a Bearer token:
- `POST /api/v1/pipeline/run`
- `POST /api/v1/pipeline/run/infections`
- `POST /api/v1/ai/query`

Default credentials: `admin` / `datapulse2024`

**Start PostgreSQL:**
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
| POST | `/api/v1/pipeline/run` | Triggers CMS hospital data ingestion and logs execution results |
| POST | `/api/v1/pipeline/run/infections` | Triggers healthcare-associated infections data ingestion |
| GET | `/api/v1/hospitals` | Returns a paginated list of hospitals. Supports `page`, `limit`, `state`, and `search` filters |
| GET | `/api/v1/hospitals/{facility_id}` | Returns a single hospital by facility ID |
| GET | `/api/v1/hospitals/metrics/rating-distribution` | Returns average hospital rating per state, ordered by rating |
| GET | `/api/v1/infections` | Lists healthcare-associated infection records. Supports `state`, `compared_to_national`, `page`, `limit` filters |
| GET | `/api/v1/infections/{facility_id}` | Returns all infection measures for a specific hospital |
| GET | `/api/v1/physicians` | On-demand physician search. Supports `state`, `specialty`, `name`, `limit` filters |
| GET | `/api/v1/physicians/state-analysis/{state}` | Physician-hospital correlation analysis by state |
| GET | `/api/v1/physicians/scarce-specialties/{state}` | Returns top 10 scarce medical specialties compared to national average |
| GET | `/api/v1/physicians/cache-status` | Returns status of national specialty cache in Redis |
| POST | `/api/v1/physicians/warm-cache` | Triggers background population of national specialty counts cache |
| POST | `/api/v1/ai/query` | Accepts a natural language question and returns SQL, results, and explanation. Requires JWT. |
| POST | `/api/v1/auth/token` | Returns a JWT access token. Credentials: `admin` / `datapulse2024` |


**Example:**

GET /api/v1/hospitals?page=1&limit=20&state=MA


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

DataPulse includes a natural language query interface powered by a local LLM via Ollama.

## Physician & Hospital Analysis

DataPulse integrates the CMS Doctors and Clinicians dataset (3.3M+ records) on-demand — without local storage — to analyze the relationship between physician density and hospital quality by state.

**Why on-demand instead of ingestion?**
The physician dataset contains 3.3M+ records with no direct foreign key relationship to hospitals. Storing it locally would require significant infrastructure (partitioned tables, specialized indexes) without proportional analytical benefit for the current scope. On-demand queries via the CMS API return results in milliseconds for filtered requests.

**Why Pandas instead of Spark?**
At 3.3M records, Pandas handles the analytical workload efficiently on a single machine. Spark would add infrastructure complexity (cluster setup, serialization overhead) without performance gains at this scale. The right tool for the right job — Spark becomes relevant at billions of records or distributed processing requirements.

**Available analysis:**
- Physician count per state (sourced live from CMS)
- Average hospital rating per state (from local database)
- Physicians per hospital ratio
- Cached for 1 hour per state to minimize API calls

**How it works:**

1. User submits a question in natural language
2. LLM receives the question alongside the database schema as context
3. LLM generates a valid PostgreSQL SELECT query
4. Query is executed against the database
5. LLM explains the results in the user's language

**Features:**
- Multilingual support — responds in the same language as the question
- SELECT-only enforcement — only read queries are allowed, preventing any data modification
- Local LLM — runs entirely on your machine via Ollama, no external API calls or costs

**Model:** llama3.1 (via Ollama)

**Example:**
```json
POST /api/v1/ai/query
{
    "question": "Which states have the most 5-star hospitals?"
}
```

**Setup:**
```bash
# Install Ollama from https://ollama.com/download
ollama pull llama3.1
```

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

**AI multi-schema queries**
The AI layer knows the schema of both `hospitals` and `hospital_infections` tables, enabling cross-table queries via JOIN. Example: "Which hospitals in Ohio have worse than national benchmark infections?" generates a JOIN query automatically.

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
The AI query endpoint is limited to 5 requests per minute per IP using `slowapi`. This prevents abuse of the local LLM which is computationally expensive.

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
Every execution is recorded from start to finish. Each run tracks status (`running`, `success`, `failed`), record counts, and error messages if applicable — making it easy to monitor data freshness and diagnose failures.

**PostgreSQL**
Open source, OLTP-optimized, and well-supported by SQLAlchemy with async drivers. A natural fit for structured healthcare data with relational integrity requirements.

## Future Improvements

- Schedule pipeline runs with Prefect or Dagster
- Add data quality check with Great Expectations
- Expand AI layer with RAG for document-based queries
- Specialty scarcity analysis — identify underserved specialties by state
- Spark pipeline for large-scale batch processing of physician data
- Scheduled pipeline runs with Prefect or Dagster
- Elasticsearch for advanced full-text search
- pg_trgm index already implemented for fuzzy hospital name search