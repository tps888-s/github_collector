---

# GitHub Commit Data Collector

This project collects comprehensive commit data from GitHub repositories, storing metadata in **CSV files** and file contents locally. This data is perfect for training Machine Learning models focused on code changes, author behavior, or project evolution. The collection process is automated using **Apache Airflow**.

## Features

* **Flexible Data Schema**: Stores commit metadata (author, message, dates, file changes, lines added/deleted) in structured **CSV files**.
* **Local File Content Storage**: Captures the state of individual files **before and after** a commit, saving them directly to your local file system. This allows for detailed analysis of code changes.
* **Repository State Restoration**: The collected commit SHAs and local file paths enable you to restore the exact state of a repository or individual files at any given commit.
* **Filtering Capabilities**: The metadata includes metrics like **number of files/lines changed** and **file types**, allowing for targeted data extraction for ML tasks.
* **Scalable Data Ingestion**: An **Apache Airflow pipeline** automates the data collection process, enabling regular and incremental updates from numerous GitHub repositories.

## Getting Started

### Prerequisites

* Python 3.8+
* Git installed locally
* GitHub Personal Access Token (PAT) with `repo` scope (for public repos, `public_public` is sufficient)
* Apache Airflow (for orchestration)

### Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd github-commit-data-collector
    ```
2.  **Install Python Dependencies**:
    ```bash
    pip install PyGithub gitpython
    ```
3.  **Configure Environment Variables**: Create a `.env` file or set environment variables for your GitHub PAT and local storage paths:
    ```
    # .env example
    GITHUB_TOKEN="ghp_YOUR_PERSONAL_ACCESS_TOKEN"
    LOCAL_REPO_BASE_PATH="/path/to/your/local/git_repos"
    LOCAL_FILE_BLOBS_BASE_PATH="/path/to/your/local/file_blobs"
    LOCAL_RAW_DIFFS_BASE_PATH="/path/to/your/local/raw_diffs" # Optional, if you store raw diffs
    CSV_OUTPUT_BASE_PATH="/path/to/your/local/csv_data"
    ```
    **Ensure these local paths exist and have sufficient disk space.**
4.  **Airflow Integration**: Place the Airflow DAG files (`repo_discovery_dag.py`, `commit_collector_dag.py`) into your Airflow `dags` folder.

## Usage

1.  **Start Airflow**: Ensure your Airflow scheduler and webserver are running.
2.  **Enable DAGs**: From the Airflow UI, enable the `github_repo_discovery` and `github_commit_incremental_collector` DAGs.
3.  **Monitor**: Observe the Airflow logs and your specified local storage directories (e.g., `/tmp/github_repos`, `/tmp/github_file_blobs`, `/tmp/github_csv_data` if using default `/tmp` paths) for collected data.

The `github_repo_discovery` DAG will periodically find and add new repositories to your `repositories.csv` file, while the `github_commit_incremental_collector` DAG will regularly fetch and store new commit data and file contents for those repositories.

## Data Schema (CSV Files)

* `repositories.csv`: Stores metadata about each GitHub repository.
* `commits.csv`: Contains details for each commit, including author, message, and summary statistics.
* `commit_files.csv`: Links commits to the files they changed, providing granular details like additions, deletions, and local paths to the file's content before and after the commit.

---