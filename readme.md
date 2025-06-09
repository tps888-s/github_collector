
# GitHub Commit Data Collector

This project collects comprehensive commit data from GitHub repositories, storing metadata in CSV files and file contents locally. This data is perfect for training Machine Learning models focused on code changes, author behavior, or project evolution. The collection process may be  automated using Apache Airflow.

## Features

* Flexible Data Schema: Stores commit metadata (author, message, dates, file changes, lines added/deleted) in structured CSV files.
* Local File Content Storage: Captures the state of individual files before and after a commit, saving them directly to your local file system. This allows for detailed analysis of code changes.
* Repository State Restoration: The collected commit SHAs and local file paths enable you to restore the exact state of a repository or individual files at any given commit.
* Filtering Capabilities: The metadata includes metrics like number of files/lines changed and file types, allowing for targeted data extraction for ML tasks.
* Scalable Data Ingestion: An Apache Airflow pipeline automates the data collection process, enabling regular and incremental updates from numerous GitHub repositories.

## Getting Started

### Prerequisites

* Python 3.8+
* Git installed locally
* GitHub Personal Access Token (PAT) with `repo` scope (for public repos, `public_public` is sufficient)
* Apache Airflow (for orchestration)

### Setup

1.  Clone the Repository:
    ```bash
    git clone https://github.com/tps888-s/github_collector.git
    cd github_collector
    ```
2.  Install Python Dependencies:
    ```bash
    pip install PyGithub gitpython
    ```
3.  Configure Environment Variables: Update a `config.py` file or use existing values:
    ```
    #example
    GITHUB_TOKEN="ghp_YOUR_PERSONAL_ACCESS_TOKEN"
    LOCAL_REPO_BASE_PATH="/path/to/your/local/git_repos"
    LOCAL_FILE_BLOBS_BASE_PATH="/path/to/your/local/file_blobs"
    LOCAL_RAW_DIFFS_BASE_PATH="/path/to/your/local/raw_diffs" # Optional
    CSV_OUTPUT_BASE_PATH="/path/to/your/local/csv_data"
    ```
    Ensure these local paths exist and have sufficient disk space.

## Data Schema (CSV Files)

* `repositories.csv`: Stores metadata about each GitHub repository.
* `commits.csv`: Contains details for each commit, including author, message, and summary statistics.
* `commit_files.csv`: Links commits to the files they changed, providing granular details like additions, deletions, and local paths to the file's content before and after the commit.

## Detailed schema description
    schema/schema.md

## DAGs examples
    dags/repo_discovery_dag.py *Discovering Repositories*
    dags/commit_collector_dag.py *Processes commits for repository(-ies).*

## Overall Strategy:
    Identify Target Repositories: Decide on criteria for selecting repositories (e.g., language, stars, activity, specific organizations).
    GitHub API Access: Obtain a GitHub Personal Access Token (PAT) with appropriate permissions.
    Data Ingestion Pipeline: Develop a robust application/script to:
    Fetch repository metadata.
    Clone repositories (or use Git API for lightweight data).
    Iterate through commit history.
    Extract commit details, file changes, and file contents.
    Transform data into the defined schema.
    Storage: Utilize S3-like object storage for raw file content and a database for structured metadata.