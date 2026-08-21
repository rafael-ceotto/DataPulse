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
| POST | `/api/v1/pipeline/run` | Triggers CMS data ingestion and logs execution results |
| GET | `/api/v1/hospitals` | Returns a paginated list of hospitals. Supports `page`, `limit`, and `state` filters |
| GET | `/api/v1/hospitals/{facility_id}` | Returns a single hospital by facility ID |

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

## Technical Decisions

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

- Schedule pipeline runs with Prefect or Dragster
- Add data quality check with Great Expectations
- Expand AI layer with RAG for document-based queries