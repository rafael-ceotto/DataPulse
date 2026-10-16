FROM python:3.13-slim

WORKDIR /app

RUN pip install dbt-postgres

COPY . .

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["dbt", "run", "--profiles-dir", "/app"]