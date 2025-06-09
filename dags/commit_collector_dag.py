from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

from ..src.github_collector import get_repos_for_processing, process_single_repository

with DAG(
    dag_id='github_commit_incremental_collector',
    start_date=days_ago(1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['github', 'data_ingestion', 'commits', 'csv'],
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'max_active_runs': 1
    }
) as dag:

    def _get_repos_to_process_callable(ti, **kwargs):
        """Callable for the get_repos_to_process task."""
        repos_full_names = get_repos_for_processing(
            batch_size=kwargs.get('batch_size', 5),
            last_fetched_threshold_hours=kwargs.get('last_fetched_threshold_hours', 1)
        )
        ti.xcom_push(key='repos_to_process', value=repos_full_names)
        return repos_full_names

    get_repos_task = PythonOperator(
        task_id='get_repos_to_process',
        python_callable=_get_repos_to_process_callable,
        op_kwargs={
            'batch_size': 5,
            'last_fetched_threshold_hours': 1
        }
    )

    def _process_single_repository_callable(repo_full_name, **kwargs):
        """Callable for processing a single repository."""
        process_single_repository(repo_full_name) # github_collector function directly handles CSV

    process_repo_task = PythonOperator(
        task_id='process_repository_commits',
        python_callable=_process_single_repository_callable,
        op_args=["{{ task_instance.xcom_pull(task_ids='get_repos_to_process')[_TI_MAP_KEY_] }}"],
    ).expand(
        xcom_pull_args={'task_ids': 'get_repos_to_process', 'key': 'repos_to_process'}
    )

    get_repos_task >> process_repo_task