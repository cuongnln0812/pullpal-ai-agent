from agents.state import PRFetcherAgentState
from github_fetcher import fetch_pr_files, parse_github_pr_url, parse_pr_files, fetch_repo_context



def pr_fetcher_agent(state: PRFetcherAgentState) -> PRFetcherAgentState:
    """
    PR Fetcher Agent.

    Fetches files from a GitHub PR and repository context for better code understanding.

    Args:
        state (PRFetcherAgentState): The current state containing the PR URL and optional token.

    Returns:
        PRFetcherAgentState: Updated state with PR info, parsed files, and repo context.
    """
    # Parse PR URL
    pr_info = parse_github_pr_url(state.pr_url)

    # Fetch raw PR files using optional token
    raw_files = fetch_pr_files(
        owner=pr_info["owner"],
        repo=pr_info["repo"],
        pr_number=pr_info["pr_number"],
        token=state.token
    )

    # Parse files into normalized format
    parsed_files = parse_pr_files(raw_files)

    # Fetch repository context for better code understanding
    print(f"📚 Fetching repository context for {pr_info['owner']}/{pr_info['repo']}...")
    repo_context = fetch_repo_context(
        owner=pr_info["owner"],
        repo=pr_info["repo"],
        token=state.token or state.github_token
    )

    # Update state
    state.owner = pr_info["owner"]
    state.repo = pr_info["repo"]
    state.pr_number = pr_info["pr_number"]
    state.files = parsed_files
    state.repo_context = repo_context

    return state