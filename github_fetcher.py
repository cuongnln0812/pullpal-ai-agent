import os
import re
import requests
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs

GITHUB_API = "https://api.github.com"


def parse_github_pr_url(url: str) -> Dict[str, Union[str, int, None]]:
    """
    Parse a GitHub Pull Request URL into components.

    Args:
        url (str): Example: https://github.com/user/repo/pull/123?page=2

    Returns:
        dict: {"owner": str, "repo": str, "pr_number": int, "page": Optional[int]}
    """
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        raise ValueError("Invalid GitHub URL")

    match = re.match(r"^/([^/]+)/([^/]+)/pull/(\d+)", parsed.path)
    if not match:
        raise ValueError("URL does not look like a PR link")

    owner, repo, pr_number = match.groups()
    query_params = parse_qs(parsed.query)

    page = None
    if "page" in query_params:
        try:
            page = int(query_params["page"][0])
        except (ValueError, IndexError):
            page = None

    return {
        "owner": owner,
        "repo": repo,
        "pr_number": int(pr_number),
        "page": page,
    }


def fetch_pr_files(
    owner: str, repo: str, pr_number: int, token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch changed files from a GitHub Pull Request.

    Args:
        owner (str): Repository owner
        repo (str): Repository name
        pr_number (int): Pull request number
        token (str, optional): GitHub personal access token for private repos

    Returns:
        List[Dict[str, Any]]: List of file information dictionaries
    """
    headers = {}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    files, page = [], 1
    while True:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files?page={page}&per_page=100"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 403 and "X-RateLimit-Remaining" in resp.headers:
            reset_time = resp.headers.get("X-RateLimit-Reset")
            raise RuntimeError(
                f"GitHub API rate limit exceeded. Reset at {reset_time}."
            )

        resp.raise_for_status()
        data = resp.json()
        if not data:
            break

        files.extend(data)
        if len(data) < 100:
            break
        page += 1

    return files


def parse_pr_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize raw PR file data.

    Args:
        files (List[Dict]): Raw GitHub PR files JSON

    Returns:
        List[Dict]: Parsed file info
    """
    return [
        {
            "filename": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
            "patch": f.get("patch", ""),   # may be missing for binary/large files
            "truncated": "patch" not in f,
        }
        for f in files
    ]

# for testing this file

if __name__ == "__main__":
    url = "https://github.com/dharampatel/medical-knowledge-assistant/pull/1"
    result = parse_github_pr_url(url)
    files = fetch_pr_files(result["owner"], result["repo"], result["pr_number"])
    parsed = parse_pr_files(files)

    for f in parsed:
        print(f"\n--- {f['filename']} ({f['status']}) ---\n{f['patch'][:500]}...")