FROM python:3.13-slim

WORKDIR /app

RUN pip install dbt-postgres

COPY . .

CMD ["dbt", "run", "--profiles-dir", "/app"]