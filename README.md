A colleague of mine lost her parents in the same week. Both went to hospitals that didn't have what they needed.

My grandmother went through something similar. When she broke her leg, the public ambulance was about to take her to the nearest hospital. Not the most appropriate one, and definitely, not the one she needed due to her other condition. By that time, we were lucky enough to have means to transport her with a private ambulance instead of the public one and send her to the chosen hospital.

It's been a while and trust me when I say that stills haunts me.

That's why I built DataPulse.

The idea is straightforward: CMS (Centers for Medicare & Medicaid Services) data is public, and it has everything you need to make an informed decision about where to get treated. DataPulse takes that data, processes it, validates it, and exposes it in a way anyone can use, whether you're a patient looking for the best hospital for a rare cancer, or a health administrator analyzing the quality of an entire network.

Think about it this way: if you have a rare cancer and there's a specialized oncology hospital in Arizona, why would you settle for a generic one closer to home? With DataPulse, you have that information before you need it.

## What it does

DataPulse ingests, validates, and transforms data from 5,419 hospitals and 96,055 hospital infection records from CMS. All of that feeds an API that exposes quality metrics, physician analysis by state, scarce specialties, and a search interface that works both with direct SQL queries and an AI agent that knows when to go beyond internal data.

The part I'm most proud of isn't the most obvious one. It's not the pipeline, and it's not the agent. It's the scarce specialty analysis! Knowing that a state has less than 50% of the specialists it should have is the kind of information that can save a life. If someone opens DataPulse and uses that before choosing where to get treated, the project was worth it.

---

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, httpx
- **AI:** Groq API (openai/gpt-oss-120b) with tool calling and web search via Tavily
- **Caching:** Redis
- **Testing:** pytest, pytest-asyncio
- **Infrastructure:** Docker, Docker Compose, GitHub Actions
- **Frontend:** React + Vite
- **Integrations:** Slack, Notion, GitHub

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

    subgraph Storage["Storage"]
        PG[(PostgreSQL)]
        Redis[(Redis Cache)]
    end

    subgraph ExternalData["External Data Sources"]
        CMS[CMS API]
        Physicians[CMS Physicians API]
    end

    subgraph AI["AI & Search"]
        Groq[Groq API\nopenai/gpt-oss-120b]
        Tavily[Tavily\nWeb Search]
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

    Pipeline --> CMS
    Pipeline --> Physicians
    Pipeline --> PG
    Pipeline --> Groq
    Pipeline --> Slack
    Pipeline --> NotionAPI
    Pipeline --> GitHub

    Scheduler -->|every 6h| Pipeline

    Router --> PG
    Router --> Redis

    UI -->|polling 60s| GHActions
```

The pipeline follows **Medallion Architecture** principles:
- **Bronze:** raw CSV data fetched directly from CMS
- **Silver:** validated and typed via Pydantic
- **Gold:** clean records in PostgreSQL, ready for consumption

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
```

All integrations are optional. The pipeline and AI work without them.

---

## How to run

### With Docker (recommended)

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the API, and the frontend in one command. The frontend is available at `http://localhost` and the API at `http://localhost:8000`.

To rebuild only what changed:

```bash
docker compose up --build frontend -d  # frontend changes
docker compose up --build api -d       # backend changes
```

### Locally

```bash
# Start only the database and Redis
docker compose up db redis -d

# Install dependencies
poetry install

# Run migrations
cd backend
alembic upgrade head

# Start the API
uvicorn app.main:app --reload

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

API docs at `http://localhost:8000/docs`.

### Authentication

Protected POST endpoints require a Bearer token:

POST /api/v1/auth/token
username: admin
password: datapulse2024


---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Health check |
| POST | `/api/v1/pipeline/run` | Triggers hospital data ingestion |
| POST | `/api/v1/pipeline/run/infections` | Triggers infection data ingestion |
| GET | `/api/v1/pipeline/runs` | Execution history with AI-generated insights |
| GET | `/api/v1/hospitals` | Paginated hospital list. Supports `page`, `limit`, `state`, `search`, `min_rating` |
| GET | `/api/v1/hospitals/export` | All hospitals in a state without pagination. Requires `state` |
| GET | `/api/v1/hospitals/data-quality` | Data quality metrics: completeness, unrated, low-rated |
| GET | `/api/v1/hospitals/{facility_id}` | Hospital by facility ID |
| GET | `/api/v1/hospitals/metrics/rating-distribution` | Average rating by state |
| GET | `/api/v1/infections` | Infection records. Supports `state`, `compared_to_national`, `page`, `limit` |
| GET | `/api/v1/infections/{facility_id}` | Infections for a specific facility |
| GET | `/api/v1/physicians` | Physician search. Supports `state`, `specialty`, `name`, `limit` |
| GET | `/api/v1/physicians/state-analysis/{state}` | Physician-hospital correlation by state |
| GET | `/api/v1/physicians/scarce-specialties/{state}` | Top 10 scarce specialties vs national average |
| GET | `/api/v1/physicians/cache-status` | Specialty cache status |
| POST | `/api/v1/physicians/warm-cache` | Populates specialty cache in background |
| POST | `/api/v1/ai/query` | Natural language query. Requires JWT |
| POST | `/api/v1/notion/save` | Saves an insight to Notion. Requires JWT |
| POST | `/api/v1/auth/token` | Returns a JWT |

---

## Testing

```bash
pytest -v                    # all tests
pytest tests/unit -v         # unit tests
pytest tests/integration -v  # integration tests
pytest tests/api -v          # API tests
```

---

## The AI layer

This is the part that evolved the most during development. The agent isn't a chatbot. It's an analyst with access to real data that knows when it needs to look beyond the database.

It operates in two modes:

**SQL mode** — for direct questions. "Which hospitals have 5 stars in Ohio?" becomes a SELECT query and returns the data.

**Agent mode** — for complex analysis. "Why do hospitals in Utah have higher ratings than the national average?" triggers a tool calling loop: it pulls the rating distribution from the database, then goes to the web for external context, and synthesizes everything into a coherent response.

What I find most interesting is that the agent decides on its own which mode to use, and when it needs web search, it uses it. It's not a static RAG; it's a system that knows when internal data isn't enough.

**Available tools:**
- `search_hospitals` — hospitals by state
- `get_top_rated_hospitals` — highest or lowest rated
- `get_rating_distribution` — average rating by state
- `get_physician_state_analysis` — physicians and hospitals by state
- `get_scarce_specialties` — scarce specialties
- `get_hospital_infections` — HAI infection summary by state
- `web_search` — external search via Tavily

Any response can be saved to Notion with one click.

---

## Automatic insights

After every pipeline run, the system automatically generates an insight about the data using Groq. What makes this different from a simple summary is that the agent considers the last 5 previous insights before generating the next one so it reasons about trends, not just the current moment.

After generating, the insight goes to three places: the database (shows up in the Pipeline Runs dashboard), Slack (as an alert), and the repository (as a commit to `insights.md`).

---

## Scheduled pipeline

The scheduler runs the full pipeline every 6 hours without any manual intervention. I chose APScheduler over Celery or Prefect because at this scale an in-process scheduler is simpler, cheaper, and doesn't add unnecessary infrastructure.

---

## Integrations

**Slack** — alert after each pipeline run with the average rating, variation from the previous run, and the generated insight.

**Notion** — any AI Query response can be saved to a Notion page with one click. It saves the question, tools used, and full explanation as structured blocks.

**GitHub** — insights are automatically committed to `insights.md`, creating a living record of data quality trends over time.

**CI badge** — the frontend header shows the latest CI status in real time, polling every 60 seconds via the public GitHub API.

---

## Data quality

The current CMS dataset has ~58.6% completeness — 41.4% of hospitals don't have an overall rating. That's not a bug, it's a known limitation of the public data. DataPulse surfaces this transparently in the Data Quality dashboard, alongside alerts for low-rated hospitals and missing fields.

---

## Technical decisions

**Why APScheduler and not Celery?** At this scale, adding a broker and separate workers would be over-engineering. The scheduler runs in the same process as the API with zero overhead.

**Why not classic RAG?** The agent with web search is more honest about what it knows and what it doesn't. A static RAG would answer with what it has; the agent goes looking when it needs to.

**Upsert instead of delete+insert** — CMS updates its data periodically. With `INSERT ... ON CONFLICT DO UPDATE`, the pipeline can run as many times as needed without creating duplicates.

**Sampling for specialty analysis** — instead of fetching 3.3M physician records nationally, we sample 50,000 and extrapolate. This reduces API calls from ~2,200 to ~33 while maintaining statistical significance.

**Three CSV export modes** — current page, all hospitals in a state, or only the ones the user expanded (with infection data included).

---

## What's next

- Slack alerts when data completeness drops below a threshold
- RAG over CMS policy documents
- Elasticsearch for advanced full-text search