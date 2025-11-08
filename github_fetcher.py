import os
import re
import time
import math
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

    files: List[Dict[str, Any]] = []
    page = 1

    # Retry/backoff configuration
    max_attempts = 4
    base_backoff = 1.0  # seconds
    max_auto_wait = int(os.getenv("GITHUB_MAX_AUTO_WAIT", "300"))  # seconds

    while True:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files?page={page}&per_page=100"

        attempt = 0
        while True:
            try:
                resp = requests.get(url, headers=headers, timeout=30)
            except requests.RequestException as e:
                attempt += 1
                if attempt >= max_attempts:
                    raise
                sleep = base_backoff * (2 ** (attempt - 1))
                time.sleep(sleep)
                continue

            # Handle rate limit explicitly
            if resp.status_code == 403 and "X-RateLimit-Remaining" in resp.headers:
                remaining = resp.headers.get("X-RateLimit-Remaining")
                reset_header = resp.headers.get("X-RateLimit-Reset")
                try:
                    reset_ts = int(reset_header) if reset_header else None
                except Exception:
                    reset_ts = None

                if remaining == "0" and reset_ts:
                    now_ts = int(time.time())
                    wait = max(0, reset_ts - now_ts)
                    # If wait is short, auto-sleep; otherwise surface helpful error
                    if wait <= max_auto_wait:
                        print(f"GitHub rate limit reached; sleeping {wait}s until reset...")
                        time.sleep(wait + 1)
                        # after sleeping, retry the same page
                        continue
                    else:
                        reset_time_str = reset_header
                        raise RuntimeError(
                            f"GitHub API rate limit exceeded. Reset at {reset_time_str} (in ~{wait}s). "
                            "Set a GITHUB_TOKEN environment variable to increase rate limits, or wait until reset."
                        )

            # For other 403/4xx/5xx errors, do exponential backoff a few times
            if resp.status_code >= 400:
                attempt += 1
                if attempt >= max_attempts:
                    # Surface a useful message for 404/403
                    try:
                        resp.raise_for_status()
                    except Exception:
                        raise
                sleep = base_backoff * (2 ** (attempt - 1))
                time.sleep(sleep)
                continue

            # Success
            break

        data = resp.json()
        if not data:
            break

        files.extend(data)
        if len(data) < 100:
            break
        page += 1

    return files


def fetch_repo_context(
    owner: str, repo: str, token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch repository context for better code understanding.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        token (str, optional): GitHub personal access token
        
    Returns:
        Dict[str, Any]: Repository context including README, languages, structure
    """
    headers = {}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    
    context = {
        "readme": None,
        "languages": {},
        "description": None,
        "topics": [],
        "package_files": {},
        "project_structure": []
    }
    
    try:
        # Get repository metadata
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        repo_resp = requests.get(repo_url, headers=headers, timeout=10)
        if repo_resp.status_code == 200:
            repo_data = repo_resp.json()
            context["description"] = repo_data.get("description", "")
            context["topics"] = repo_data.get("topics", [])
            context["default_branch"] = repo_data.get("default_branch", "main")
        
        # Get README
        readme_url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
        readme_resp = requests.get(readme_url, headers=headers, timeout=10)
        if readme_resp.status_code == 200:
            readme_data = readme_resp.json()
            # Decode base64 content
            import base64
            readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8")
            # Truncate if too long (keep first 3000 chars for context)
            context["readme"] = readme_content[:3000] if len(readme_content) > 3000 else readme_content
        
        # Get programming languages
        lang_url = f"{GITHUB_API}/repos/{owner}/{repo}/languages"
        lang_resp = requests.get(lang_url, headers=headers, timeout=10)
        if lang_resp.status_code == 200:
            context["languages"] = lang_resp.json()
        
        # Get key package/config files for tech stack detection
        key_files = [
            "package.json", "requirements.txt", "pom.xml", "build.gradle",
            "Cargo.toml", "go.mod", "composer.json", "Gemfile", "pyproject.toml"
        ]
        
        for filename in key_files:
            try:
                file_url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{filename}"
                file_resp = requests.get(file_url, headers=headers, timeout=5)
                if file_resp.status_code == 200:
                    file_data = file_resp.json()
                    import base64
                    content = base64.b64decode(file_data.get("content", "")).decode("utf-8")
                    # Store first 1000 chars
                    context["package_files"][filename] = content[:1000]
            except Exception:
                continue
        
        # Get repository tree (directory structure) - limited depth
        try:
            tree_url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{context['default_branch']}?recursive=1"
            tree_resp = requests.get(tree_url, headers=headers, timeout=10)
            if tree_resp.status_code == 200:
                tree_data = tree_resp.json()
                tree = tree_data.get("tree", [])
                # Extract main directories and file types
                dirs = set()
                for item in tree[:100]:  # Limit to first 100 items
                    if item.get("type") == "tree":
                        path = item.get("path", "")
                        if "/" not in path:  # Top-level directories only
                            dirs.add(path)
                context["project_structure"] = sorted(list(dirs))
        except Exception:
            pass
            
    except Exception as e:
        print(f"⚠️ Could not fetch full repo context: {e}")
    
    return context


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