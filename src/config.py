import os

with open("token.txt", "r", encoding="utf-8") as file:
    token = file.read()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", token) # IMPORTANT: add file token.txt with your token

# --- Local Storage Paths for Repos, Blobs, Diffs, and CSVs ---
LOCAL_REPO_BASE_PATH = os.getenv("LOCAL_REPO_BASE_PATH", "C:\\Users\\Emily\\PycharmProjects\\github_collector\\tmp\github_repos")
LOCAL_FILE_BLOBS_BASE_PATH = os.getenv("LOCAL_FILE_BLOBS_BASE_PATH", "C:\\Users\\Emily\\PycharmProjects\\github_collector\\tmp\\github_file_blobs")
LOCAL_RAW_DIFFS_BASE_PATH = os.getenv("LOCAL_RAW_DIFFS_BASE_PATH", "C:\\Users\\Emily\\PycharmProjects\\github_collector\\tmp\\github_raw_diffs")

# --- NEW: CSV Storage Paths ---
CSV_OUTPUT_BASE_PATH = os.getenv("CSV_OUTPUT_BASE_PATH", "C:\\Users\\Emily\\PycharmProjects\\github_collector\\tmp\\github_csv_data")
REPOS_CSV_PATH = os.path.join(CSV_OUTPUT_BASE_PATH, "repositories.csv")
COMMITS_CSV_PATH = os.path.join(CSV_OUTPUT_BASE_PATH, "commits.csv")
COMMIT_FILES_CSV_PATH = os.path.join(CSV_OUTPUT_BASE_PATH, "commit_files.csv")

# Ensure all local paths exist
os.makedirs(LOCAL_REPO_BASE_PATH, exist_ok=True)
os.makedirs(LOCAL_FILE_BLOBS_BASE_PATH, exist_ok=True)
os.makedirs(LOCAL_RAW_DIFFS_BASE_PATH, exist_ok=True)
os.makedirs(CSV_OUTPUT_BASE_PATH, exist_ok=True)