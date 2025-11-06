import os
from dotenv import load_dotenv
from agents.llm_client import get_llm_client
from agents.compat import HumanMessage
from agents.state import TestCoverageAgentState

load_dotenv()

# --------------------------
# Initialize LLM client (uses HOST_URL if set, otherwise langchain)
# --------------------------
llm = get_llm_client()


def doc_summarizer_agent(state: TestCoverageAgentState) -> TestCoverageAgentState:
    """
    Doc Summarizer Agent.

    Produces a concise natural language summary of a PR's changes,
    including file changes, new functions/classes, and generated tests.

    Args:
        state (TestCoverageAgentState): Current agent state with PR files and coverage findings.

    Returns:
        TestCoverageAgentState: Updated state with `pr_summary` populated.
    """
    # --- Count file changes ---
    added = sum(1 for f in state.files if f.get("status") == "added")
    removed = sum(1 for f in state.files if f.get("status") == "removed")
    modified = sum(1 for f in state.files if f.get("status") not in ("added", "removed"))

    # --- Count new functions/classes ---
    new_entities = 0
    for f in state.files:
        patch = f.get("patch", "")
        new_entities += sum(1 for line in patch.splitlines() if line.startswith("+") and ("def " in line or "class " in line))

    # --- Count generated tests ---
    gen_tests = 0
    if hasattr(state, "coverage_findings"):
        for f in state.coverage_findings:
            gen_tests += len(f.get("generated_tests", []))

    # --- Generate summary via LLM ---
    prompt = f"""
You are an assistant that summarizes GitHub pull requests.

PR Stats:
- Files added: {added}
- Files modified: {modified}
- Files removed: {removed}
- New functions/classes: {new_entities}
- Generated test stubs: {gen_tests}

Write a concise natural language summary in 1-2 sentences.
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
    except Exception as e:
        print(f"⚠️ Doc summarizer LLM failed: {e}")
        summary = f"In this PR, {added} files were added, {modified} modified, {removed} removed, with {new_entities} new functions/classes."

    state.pr_summary = summary
    return state