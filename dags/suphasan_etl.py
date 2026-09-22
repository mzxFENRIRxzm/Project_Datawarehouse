"""Daily PostgreSQL maintenance DAG without an external OLAP database."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator


default_args = {
    "owner": "suphasan-data-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="suphasan_daily_etl",
    default_args=default_args,
    description="Daily PostgreSQL pipeline",
    schedule="0 19 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["suphasan", "postgresql"],
    max_active_runs=1,
) as dag:
    start = EmptyOperator(task_id="start")
    finish = EmptyOperator(task_id="finish")
    start >> finish
