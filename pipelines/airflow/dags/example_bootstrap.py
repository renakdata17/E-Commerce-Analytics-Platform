"""Example DAG stub — extend with prod operators (dbt, sensors, alerting)."""

from datetime import timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.utils.dates import days_ago

    def noop() -> None:
        """Replace with nightly dbt/Airbyte/quality orchestration."""

    DEFAULT_ARGS = {
        "owner": "data-platform",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }

    with DAG(
        dag_id="ecommerce_daily_bootstrap",
        default_args=DEFAULT_ARGS,
        schedule_interval="@daily",
        start_date=days_ago(1),
        catchup=False,
        tags=["ecommerce"],
    ):
        PythonOperator(task_id="placeholder", python_callable=noop)
except ImportError:  # local clone without Airflow installed
    pass
