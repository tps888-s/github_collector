import os
import datetime
import uuid

from github import Github, GithubException
from git import Repo, InvalidGitRepositoryError, GitCommandError
import logging
import time
import csv
import json # For metadata column

# --- UPDATED IMPORTS ---
from config import (
    GITHUB_TOKEN,
    LOCAL_REPO_BASE_PATH,
    LOCAL_FILE_BLOBS_BASE_PATH,
    LOCAL_RAW_DIFFS_BASE_PATH,
    REPOS_CSV_PATH,
    COMMITS_CSV_PATH,
    COMMIT_FILES_CSV_PATH
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize GitHub API client
gh = Github(GITHUB_TOKEN)

# --- CSV Headers (Manual definition as no ORM) ---
REPOS_CSV_HEADERS = [
    'id', 'owner', 'name', 'full_name', 'url', 'clone_url', 'default_branch',
    'description', 'stars', 'forks', 'created_at', 'last_fetched_at'
]
COMMITS_CSV_HEADERS = [
    'id', 'repo_id', 'sha', 'author_name', 'author_email', 'author_date',
    'committer_name', 'committer_email', 'committer_date', 'message',
    'tree_sha', 'parent_shas', 'num_files_changed', 'lines_added',
    'lines_deleted', 'url', 'diff_local_path', 'metadata'
]
COMMIT_FILES_CSV_HEADERS = [
    'id', 'commit_id', 'file_path', 'status', 'additions', 'deletions',
    'changes', 'patch', 'previous_filename', 'file_type',
    'blob_before_local_path', 'blob_after_local_path', 'metadata'
]

def get_file_type(filename):
    """Simple function to get file extension."""
    _, ext = os.path.splitext(filename)
    return ext[1:] if ext else None

def save_file_locally(file_path, content):
    """Saves content to a local file and returns the file path."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content.encode('utf-8'))
        return file_path
    except Exception as e:
        logging.error(f"Failed to save file locally: {file_path}. Error: {e}")
        return None

def write_csv_row(file_path, headers, data_row, append=True):
    """Writes a single row to a CSV file."""
    mode = 'a' if append and os.path.exists(file_path) else 'w'
    with open(file_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if mode == 'w': # Write header only if creating a new file
            writer.writeheader()
        writer.writerow(data_row)

def read_csv_data(file_path):
    """Reads all data from a CSV file into a list of dictionaries."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def update_csv_data(file_path, headers, identifier_field, new_data_row):
    """
    Reads CSV, updates a row based on identifier_field, and rewrites the CSV.
    This is inefficient for large files and should be used cautiously.
    """
    all_data = read_csv_data(file_path)
    updated = False
    for i, row in enumerate(all_data):
        if row.get(identifier_field) == str(new_data_row[identifier_field]):
            # Merge new_data_row into existing row, converting types where necessary
            for key, value in new_data_row.items():
                if isinstance(value, datetime.datetime):
                    row[key] = value.isoformat() # Convert datetime to string
                elif isinstance(value, list):
                    row[key] = json.dumps(value) # Convert list to JSON string
                elif isinstance(value, dict):
                    row[key] = json.dumps(value) # Convert dict to JSON string
                else:
                    row[key] = str(value) # Ensure all values are strings for CSV
            updated = True
            break
    if not updated:
        # Append if not found
        all_data.append(new_data_row)

    # Rewrite the entire file
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in all_data:
            # Ensure all values are stringified for writing
            sanitized_row = {k: (v.isoformat() if isinstance(v, datetime.datetime)
                                else json.dumps(v) if isinstance(v, (list, dict))
                                else str(v)) for k, v in row.items()}
            writer.writerow(sanitized_row)

def clone_or_pull_repo(repo_full_name, clone_url, local_path):
    """Clones a repo if it doesn't exist, otherwise pulls."""
    try:
        os.makedirs(local_path, exist_ok=True)
        repo = Repo(local_path)
        origin = repo.remotes.origin
        origin.pull()
        logging.info(f"Pulled latest for {repo_full_name}")
    except InvalidGitRepositoryError:
        logging.info(f"Cloning {repo_full_name} into {local_path}")
        Repo.clone_from(clone_url, local_path)
        repo = Repo(local_path)
    return repo

def process_single_repository(repo_full_name_str: str):
    """
    Processes commits for a single repository.
    Fetches new commits, extracts data, stores in CSV and LOCAL FILES.
    """
    logging.info(f"Starting to process repository: {repo_full_name_str}")

    # Read all existing repositories to find the current one and its last_fetched_at
    all_repos_data = read_csv_data(REPOS_CSV_PATH)
    repo_obj_csv = next((r for r in all_repos_data if r['full_name'] == repo_full_name_str), None)

    if not repo_obj_csv:
        logging.error(f"Repository {repo_full_name_str} not found in {REPOS_CSV_PATH}. Skipping.")
        return

    repo_local_path = os.path.join(LOCAL_REPO_BASE_PATH, repo_obj_csv['owner'], repo_obj_csv['name'])

    try:
        git_repo = clone_or_pull_repo(repo_full_name_str, repo_obj_csv['clone_url'], repo_local_path)
        git_repo.git.checkout(repo_obj_csv.get('default_branch') or 'main')

        gh_repo = gh.get_repo(repo_full_name_str)

        # Convert last_fetched_at from string to datetime
        last_fetched_at_str = repo_obj_csv.get('last_fetched_at')
        since_date = datetime.datetime.fromisoformat(last_fetched_at_str) if last_fetched_at_str else datetime.datetime.min

        gh_commits = gh_repo.get_commits(since=since_date, sha=repo_obj_csv.get('default_branch') or 'main')
        new_commit_shas = []
        for gh_commit in gh_commits:
            new_commit_shas.append(gh_commit.sha)
            if len(new_commit_shas) > 1000: # Limit for a single run
                logging.warning(f"Stopped fetching commits for {repo_full_name_str} after 1000 to manage resources.")
                break

        logging.info(f"Found {len(new_commit_shas)} new commits for {repo_full_name_str}")

        # Read existing commits to check for duplicates (inefficient for large files)
        existing_commits_data = read_csv_data(COMMITS_CSV_PATH)
        existing_commit_shas = {c['sha'] for c in existing_commits_data if c.get('repo_id') == repo_obj_csv['id']}

        for sha in reversed(new_commit_shas):
            if sha in existing_commit_shas:
                logging.info(f"Commit {sha} for {repo_full_name_str} already exists. Skipping.")
                continue

            try:
                gh_commit_detail = gh_repo.get_commit(sha=sha)

                commit_data = {
                    'id': str(uuid.uuid4()), # Generate UUID for CSV
                    'repo_id': repo_obj_csv['id'],
                    'sha': gh_commit_detail.sha,
                    'author_name': gh_commit_detail.author.name if gh_commit_detail.author else None,
                    'author_email': gh_commit_detail.author.email if gh_commit_detail.author else None,
                    'committer_name': gh_commit_detail.committer.name if gh_commit_detail.committer else None,
                    'committer_email': gh_commit_detail.committer.email if gh_commit_detail.committer else None,
                    'message': gh_commit_detail.commit.message,
                    'tree_sha': gh_commit_detail.commit.tree.sha,
                    'parent_shas': json.dumps([p.sha for p in gh_commit_detail.parents]), # Store as JSON string
                    'num_files_changed': gh_commit_detail.files.totalCount,
                    'lines_added': gh_commit_detail.stats.additions,
                    'lines_deleted': gh_commit_detail.stats.deletions,
                    'url': gh_commit_detail.url,
                    'diff_local_path': None, # Placeholder for full diff file path if needed
                    'metadata': json.dumps({}) # Store as JSON string
                }
                write_csv_row(COMMITS_CSV_PATH, COMMITS_CSV_HEADERS, commit_data, append=True)

                # Process files changed in the commit
                for file_change in gh_commit_detail.files:
                    file_path = file_change.filename
                    status = file_change.status
                    patch = file_change.patch
                    previous_filename = file_change.previous_filename if hasattr(file_change, 'previous_filename') else None
                    file_type = get_file_type(file_path)

                    blob_before_local_path = None
                    blob_after_local_path = None

                    file_name_for_local = file_path.replace('/', '_').replace('\\', '_')
                    repo_dir_for_blobs = os.path.join(LOCAL_FILE_BLOBS_BASE_PATH, repo_obj_csv['owner'], repo_obj_csv['name'])

                    # Get "after" state
                    try:
                        git_blob_after = git_repo.git.show(f"{sha}:{file_path}", binary=True)
                        blob_after_local_path_full = os.path.join(repo_dir_for_blobs, sha, "after", file_name_for_local)
                        blob_after_local_path = save_file_locally(blob_after_local_path_full, git_blob_after)
                    except GitCommandError as e:
                        logging.warning(f"Could not get 'after' content for {file_path} at commit {sha}: {e}")
                        blob_after_local_path = None

                    # Get "before" state
                    if status != 'added' and len(gh_commit_detail.parents) > 0:
                        parent_sha = gh_commit_detail.parents[0].sha
                        try:
                            git_blob_before = git_repo.git.show(f"{parent_sha}:{file_path}", binary=True)
                            blob_before_local_path_full = os.path.join(repo_dir_for_blobs, sha, "before", file_name_for_local)
                            blob_before_local_path = save_file_locally(blob_before_local_path_full, git_blob_before)
                        except GitCommandError as e:
                            logging.warning(f"Could not get 'before' content for {file_path} at parent {parent_sha} (commit {sha}): {e}")
                            blob_before_local_path = None

                    commit_file_data = {
                        'id': str(uuid.uuid4()),
                        'commit_id': commit_data['id'],
                        'file_path': file_path,
                        'status': status,
                        'additions': file_change.additions,
                        'deletions': file_change.deletions,
                        'changes': file_change.changes,
                        'patch': patch,
                        'previous_filename': previous_filename,
                        'file_type': file_type,
                        'blob_before_local_path': blob_before_local_path,
                        'blob_after_local_path': blob_after_local_path,
                        'metadata': json.dumps({})
                    }
                    write_csv_row(COMMIT_FILES_CSV_PATH, COMMIT_FILES_CSV_HEADERS, commit_file_data, append=True)

                logging.info(f"Successfully processed commit {sha} for {repo_full_name_str}")

            except GithubException as e:
                logging.error(f"GitHub API error for commit {sha} in {repo_full_name_str}: {e}. Retrying in 5 seconds.")
                time.sleep(5)

        # Update last_fetched_at for the repository in the CSV
        repo_obj_csv['last_fetched_at'] = datetime.datetime.now().isoformat()
        update_csv_data(REPOS_CSV_PATH, REPOS_CSV_HEADERS, 'full_name', repo_obj_csv)
        logging.info(f"Finished processing repository: {repo_full_name_str}. Updated last_fetched_at.")

    except GithubException as e:
        logging.error(f"GitHub API error for repository {repo_full_name_str}: {e}. Skipping this repo.")
    except GitCommandError as e:
        logging.error(f"Git command error for repository {repo_full_name_str}: {e}. Skipping this repo.")

def discover_and_add_repositories(query="stars:>1000", limit=10):
    """
    Discovers popular repositories using GitHub Search API and adds them to a CSV.
    """
    logging.info(f"Discovering repositories with query: '{query}' and limit: {limit}")
    all_repos_data = read_csv_data(REPOS_CSV_PATH)
    existing_repo_full_names = {r['full_name'] for r in all_repos_data}

    repos_to_add_count = 0
    new_repos_data = [] # Collect new repos before writing to avoid reading/rewriting in loop

    for repo in gh.search_repositories(query=query, sort="stars", order="desc"):
        if repos_to_add_count >= limit:
            break
        if repo.full_name not in existing_repo_full_names:
            repo_to_add = {
                'id': str(uuid.uuid4()), # Generate UUID for CSV
                'owner': repo.owner.login,
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.url,
                'clone_url': repo.clone_url,
                'default_branch': repo.default_branch,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'created_at': repo.created_at.isoformat(),
                'last_fetched_at': datetime.datetime.now().isoformat() # Mark for immediate processing
            }
            new_repos_data.append(repo_to_add)
            existing_repo_full_names.add(repo.full_name) # Add to set to prevent duplicates in current run
            repos_to_add_count += 1
        else:
            logging.info(f"Repository {repo.full_name} already exists in CSV.")

    # Append new repos to the CSV
    if new_repos_data:
        for repo_row in new_repos_data:
            write_csv_row(REPOS_CSV_PATH, REPOS_CSV_HEADERS, repo_row, append=True)
        logging.info(f"Added {len(new_repos_data)} new repositories to {REPOS_CSV_PATH}.")
    else:
        logging.info("No new repositories found to add.")


def get_repos_for_processing(batch_size=10, last_fetched_threshold_minutes=1):
    """
    Retrieves repositories from CSV that need to be processed.
    Prioritizes those not fetched recently.
    """
    all_repos_data = read_csv_data(REPOS_CSV_PATH)
    threshold_date = datetime.datetime.now() - datetime.timedelta(minutes=last_fetched_threshold_minutes)

    repos_to_process = []
    for r in all_repos_data:
        last_fetched_at_str = r.get('last_fetched_at')
        if last_fetched_at_str:
            try:
                # Handle potential Z/timezone difference if not always UTC
                last_fetched_dt = datetime.datetime.fromisoformat(last_fetched_at_str.replace('Z', '+00:00') if 'Z' in last_fetched_at_str else last_fetched_at_str)
                if last_fetched_dt <= threshold_date:
                    repos_to_process.append(r)
            except ValueError:
                logging.warning(f"Could not parse last_fetched_at: {last_fetched_at_str} for repo {r['full_name']}")
                # Treat as old if parsing fails
                repos_to_process.append(r)
        else:
            # If last_fetched_at is missing, treat as never fetched
            repos_to_process.append(r)

    # Sort by last_fetched_at (oldest first)
    repos_to_process.sort(key=lambda x: datetime.datetime.fromisoformat(x.get('last_fetched_at', datetime.datetime.min.isoformat())))

    return [r['full_name'] for r in repos_to_process[:batch_size]]

# --- Example Usage (for local testing) ---
if __name__ == "__main__":
    #print("--- Discovering Repositories ---")
    #discover_and_add_repositories(query="language:Python stars:>1000 pushed:>2025-06-08", limit=5)

    print("\n--- Getting Repositories for Incremental Processing ---")
    repos_to_update_full_names = get_repos_for_processing(batch_size=50)
    print(f"Found repos to update: {repos_to_update_full_names}")
    for repo_full_name in repos_to_update_full_names:
        process_single_repository(repo_full_name)
        print("-" * 50)