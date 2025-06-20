from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from ..src.github_collector import discover_and_add_repositories

with DAG(
    dag_id='github_repo_discovery',
    start_date=datetime(2025, 6, 1),
    schedule_interval='@weekly',
    catchup=False,
    tags=['github', 'data_ingestion', 'discovery', 'csv'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
    }
) as dag:
    discover_repos_task = PythonOperator(
        task_id='discover_and_add_popular_repositories',
        python_callable=discover_and_add_repositories,
        op_kwargs={
            'query': 'language:Python stars:>1000 pushed:>2025-06-08',
            'limit': 5
        }
    )