from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PRFetcherAgentState:
    """
    State for the PR Fetcher Agent.
    """
    pr_url: str
    token: Optional[str] = None
    owner: Optional[str] = None
    repo: Optional[str] = None
    pr_number: Optional[int] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    github_token: Optional[str] = None  # For private repo access
    # Optional project-specific coding guidelines provided by the user
    guideline_text: Optional[str] = None


@dataclass
class CodeReviewAgentState(PRFetcherAgentState):
    """
    State for the Code Review Agent.
    Inherits PRFetcherAgentState and adds code review findings.
    """
    findings: List[Dict[str, Any]] = field(default_factory=list)
    custom_guidelines: Optional[str] = None


@dataclass
class TestCoverageAgentState(CodeReviewAgentState):
    """
    State for the Test Coverage Agent.
    Inherits CodeReviewAgentState and adds coverage-related findings.
    """
    coverage_findings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PRSummaryAgentState(TestCoverageAgentState):
    """
    State for the PR Summary Agent.
    Inherits TestCoverageAgentState and adds a PR summary string.
    """
    pr_summary: Optional[str] = None