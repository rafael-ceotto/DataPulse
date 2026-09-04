from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import requests

default_args = {
    "owner": "datapulse",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def trigger_hospital_pipeline():
    token_response = requests.post(
        "http://datapulse_api:8000/api/v1/auth/token",
        data={"username": "admin", "password": "datapulse2024"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]
    
    response = requests.post(
        "http://datapulse_api:8000/api/v1/pipeline/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    result = response.json()
    print(f"Hospital pipeline: {result}")    

def trigger_infection_pipeline():
    token_response = requests.post(
        "http://datapulse_api:8000/api/v1/auth/token",
        data={"username": "admin", "password": "datapulse2024"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]

    response = requests.post(
        "http://datapulse_api:8000/api/v1/pipeline/run/infections",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    result = response.json()
    print(f"Infection pipeline: {result}")
    
with DAG(
    dag_id="datapulse_pipeline",
    default_args=default_args,
    description="DataPulse full pipeline: hospitals, infections and dbt",
    schedule_interval="0 */6 * * *",  # every 6 hours
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["datapulse", "pipeline"], 
) as dag:
    ingest_hospitals = PythonOperator(
        task_id="ingest_hospitals",
        python_callable=trigger_hospital_pipeline,
    )

    ingest_infections = PythonOperator(
        task_id="ingest_infections",
        python_callable=trigger_infection_pipeline,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "dbt run "
            "--profiles-dir /opt/airflow/dags/datapulse "
            "--project-dir /opt/airflow/dags/datapulse"
        ),
    )
    
    ingest_hospitals >> ingest_infections >> dbt_run