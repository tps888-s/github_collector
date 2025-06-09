## Proposed Data Schema:

### 1. Repositories Table
    Purpose: Stores metadata about each GitHub repository being tracked.
    Fields:
    id (Primary Key, UUID/BigInt): Unique internal identifier for the repository.
    owner (String, Indexed): GitHub username or organization name.
    name (String, Indexed): Name of the repository.
    full_name (String, Indexed): Full  Name of the repository.
    clone_url (String): URL for cloning the repository (e.g., git@github.com:owner/repo.git).
    description (String, Nullable): Repository description from GitHub.
    default_branch (String, Nullable): Repository default branch
    stars (Integer): Number of stars on GitHub.
    forks (Integer): Number of forks on GitHub.
    created_at (Timestamp): Date and time the repository was created on GitHub.
    last_fetched_at (Timestamp, Nullable): Timestamp of the last successful data ingestion for this repo.

### 2. Commits Table

    Purpose: Stores core information about each commit. This is the central entity.
    Fields:
    id(Primary Key, UUID/BigInt): Unique internal identifier for the row.
    repo_id (Foreign Key, UUID/BigInt, Indexed): Links to the Repositories table.
    sha (Primary Key, String - SHA-1 hash, Indexed): The unique SHA-1 hash of the commit.
    author_name (String, Indexed): Name of the commit author.
    author_email (String): Email of the commit author.
    committer_name (String): Name of the committer (can be different from author).
    committer_email (String): Email of the committer.
    message (Text): The full commit message.
    tree_sha (String): SHA-1 hash of the Git tree object for this commit.
    parents_shas (Array of Strings/JSONB array of SHAs): An array of commit_shas for the parent commits. Important for reconstructing history and merges.
    num_files_changed (Integer): Total number of files modified (added, changed, deleted, renamed, copied) in this commit.
    lines_added (Integer): Total lines added across all files in this commit.
    lines_deleted (Integer): Total lines deleted across all files in this commit.
    url (String): URL to the commit on GitHub.
    diff_local_path (String): Path to diff
    metadata (JSONB, Nullable): Flexible field for future, unstructured commit-level metadata (e.g., associated pull request ID, CI status).


### 3. CommitFileChanges Table
    Purpose: Links commits to the specific files they modified and stores details about that modification within the context of the commit. This captures the diff information.
    Fields:
    id(Primary Key, UUID/BigInt): Unique internal identifier for the row.    
    commit_id (Foreign Key, String, Indexed): Links to the Commits table.
    file_path (String): Representing the path of the file.
    status (String, Indexed, e.g., 'added', 'modified', 'deleted', 'renamed', 'copied'): Type of change for this file in this commit.
    additions (Integer): Lines added to this specific file in this commit.
    deletions (Integer): Lines deleted from this specific file in this commit.
    changes(Integer): Total changes
    patch(String): Patch info
    previous_filename(String): Previous file name info
    file_type(String): File type info
    blob_before_local_path(String): local path to the files for the before statement.
    blob_after_local_path(String): local path to the files for the after statement.
    metadata (JSONB, Nullable): Flexible field for future, unstructured commit-level metadata (e.g., associated pull request ID, CI status)
