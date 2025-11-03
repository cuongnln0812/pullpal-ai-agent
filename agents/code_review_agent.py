import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from agents.state import CodeReviewAgentState

load_dotenv()

# --------------------------
# Initialize Google GenAI client via LangChain
# --------------------------
client = ChatGoogleGenerativeAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    temperature=0,
    convert_system_message_to_human=True  # ensures better formatting
)

# --------------------------
# Static keyword-based issue detection
# --------------------------
STATIC_ISSUES = {
    "eval": {
        "type": "security",
        "message": "Use of eval() detected.",
        "suggestion": "Replace eval() with ast.literal_eval or proper parsing."
    },
    "print": {
        "type": "style",
        "message": "Debug print statement detected.",
        "suggestion": "Remove or replace with proper logging."
    },
    "TODO": {
        "type": "style",
        "message": "TODO comment found.",
        "suggestion": "Resolve or remove TODOs before merge."
    },
}


def safe_parse_json(raw_text: str, filename: str) -> list:
    """
    Safely parse JSON from LLM output.
    Falls back to extracting the first valid JSON array if needed.

    Args:
        raw_text (str): Raw text output from LLM.
        filename (str): Filename being processed (for logging).

    Returns:
        list: Parsed list of issue dicts, or empty list if invalid.
    """
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON array from text
        start = raw_text.find("[")
        end = raw_text.rfind("]") + 1
        if start != -1 and end != -1:
            try:
                return json.loads(raw_text[start:end])
            except json.JSONDecodeError:
                print(f"⚠️ Still invalid JSON for {filename}")
        print(f"⚠️ Invalid JSON output for {filename}: {raw_text[:200]}...")
        return []


def code_review_agent(state: CodeReviewAgentState) -> CodeReviewAgentState:
    """
    Perform static checks and LLM-based code review on PR files.

    Args:
        state (CodeReviewAgentState): Current agent state with PR files.

    Returns:
        CodeReviewAgentState: Updated state with 'findings' populated.
    """
    findings = []

    for f in state.files:
        filename = f["filename"]
        patch = f.get("patch", "")
        file_findings = []

        # --- Static checks ---
        for keyword, issue in STATIC_ISSUES.items():
            if keyword in patch:
                file_findings.append(issue)

        # Detect large files/functions
        if len(patch.splitlines()) > 200:
            file_findings.append({
                "type": "performance",
                "message": "Large file/function detected (>200 lines).",
                "suggestion": "Split into smaller, modular functions."
            })

        # --- LLM-based review (Python diffs only) ---
        if patch.strip() and filename.endswith(".py"):
            prompt = f"""
You are a senior code reviewer.
ONLY return valid JSON (no explanations, no markdown).

Analyze this GitHub PR diff for:
- Style issues
- Bugs
- Security vulnerabilities
- Performance problems

Return an array of JSON objects:
[
  {{
    "type": "style|bug|security|performance",
    "message": "string",
    "suggestion": "string"
  }}
]

Diff:
{patch}
"""
            try:
                response = client.invoke([HumanMessage(content=prompt)])
                llm_output = response.content
                llm_issues = safe_parse_json(llm_output, filename)
                if isinstance(llm_issues, list):
                    file_findings.extend(llm_issues)
            except Exception as e:
                print(f"❌ LLM review failed for {filename}: {e}")

        if file_findings:
            findings.append({
                "filename": filename,
                "issues": file_findings
            })

    state.findings = findings
    return state