FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry dbt-postgres

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root

COPY backend/app/ ./app/
COPY backend/datapulse/ ./datapulse/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]