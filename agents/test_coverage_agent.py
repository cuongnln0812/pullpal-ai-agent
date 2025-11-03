import re
import os
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import TestCoverageAgentState, CodeReviewAgentState

load_dotenv()

# --------------------------
# Initialize Google GenAI client via LangChain
# --------------------------
llm = ChatGoogleGenerativeAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    temperature=0,
    convert_system_message_to_human=True
)


def extract_added_functions(patch: str) -> list[str]:
    """
    Extract new functions and classes from a GitHub PR diff.

    Args:
        patch (str): The diff string from a PR file.

    Returns:
        list[str]: List of added function/class signatures.
    """
    added = []
    for line in patch.splitlines():
        if line.startswith("+") and ("def " in line or "class " in line):
            added.append(line[1:].strip())  # Remove leading '+'
    return added


def test_coverage_agent(state: TestCoverageAgentState) -> TestCoverageAgentState:
    """
    Test Coverage Agent.

    Detects if new/changed code has corresponding tests.
    Optionally generates pytest-style stubs for missing tests.

    Args:
        state (TestCoverageAgentState): Current state with PR files and code review findings.

    Returns:
        TestCoverageAgentState: Updated state with coverage findings.
    """
    findings = []

    # Identify test files in the PR
    changed_files = [f["filename"] for f in state.files]
    test_files = [f for f in changed_files if re.search(r"(test_|_test)\.py$", f)]

    for f in state.files:
        filename = f["filename"]
        patch = f.get("patch", "")

        # Skip obvious test files
        if re.search(r"(test_|_test)\.py$", filename):
            continue

        added_entities = extract_added_functions(patch)

        # Flag missing tests if there are added functions/classes but no test files modified
        if added_entities and not test_files:
            issue = {
                "filename": filename,
                "issue": "Missing tests",
                "message": f"New functions/classes added in {filename} but no test files were modified.",
                "suggestion": "Add unit tests in the tests/ directory.",
                "generated_tests": []
            }

            # --- Generate test stubs with LLM ---
            prompt = f"""
You are a senior Python developer.
Generate pytest-style unit test stubs for the following functions/classes
detected in the PR:

{added_entities}

Only output valid Python code, nothing else.
"""
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                issue["generated_tests"].append({
                    "filename": f"tests/test_{os.path.basename(filename)}",
                    "code": response.content.strip()
                })
            except Exception as e:
                print(f"❌ Test generation failed for {filename}: {e}")

            findings.append(issue)

    state.coverage_findings = findings
    return state