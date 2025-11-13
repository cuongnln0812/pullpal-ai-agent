import json
import os
from dotenv import load_dotenv
from agents.llm_client import get_llm_client
from agents.prompt_loader import load_prompt
from agents.compat import HumanMessage
from agents.state import CodeReviewAgentState

load_dotenv()

# --------------------------
# Initialize LLM client (uses HOST_URL if set, otherwise langchain)
# --------------------------
client = get_llm_client(convert_system_message_to_human=True)

# Load system prompt and extended rules from files
SYSTEM_PROMPT_CONTENT = ""
EXTENDED_RULES_CONTENT = ""
try:
    with open("system_prompt.md", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT_CONTENT = f.read()
    with open("extended_rules.md", "r", encoding="utf-8") as f:
        EXTENDED_RULES_CONTENT = f.read()
except FileNotFoundError as e:
    print(f"Error loading prompt/rules file: {e}. Make sure 'system_prompt.md' and 'extended_rules.md' are in the root directory.")
    # Fallback or exit if essential files are missing
    SYSTEM_PROMPT_CONTENT = "You are an expert code reviewer."
    EXTENDED_RULES_CONTENT = "Follow general coding best practices."

# --------------------------
# Language detection and best practices
# --------------------------
LANGUAGE_MAP = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell/Bash",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
}

LANGUAGE_BEST_PRACTICES = {
    "Python": [
        "Follow PEP 8 style guidelines",
        "Use type hints for function parameters and return values",
        "Use context managers (with statements) for resource management",
        "Prefer list comprehensions over map/filter for readability",
        "Use logging instead of print statements",
        "Handle exceptions appropriately, avoid bare except",
    ],
    "Java": [
        "Follow Java naming conventions (camelCase for methods/variables, PascalCase for classes)",
        "Use proper access modifiers (private, protected, public)",
        "Implement proper exception handling with specific exceptions",
        "Use @Override annotation when overriding methods",
        "Close resources properly (use try-with-resources)",
        "Avoid null, use Optional where appropriate",
        "Follow SOLID principles",
    ],
    "JavaScript": [
        "Use const/let instead of var",
        "Use === instead of == for comparisons",
        "Use arrow functions appropriately",
        "Handle promises properly (async/await or .catch())",
        "Avoid callback hell, use Promises or async/await",
        "Use proper error handling",
    ],
    "TypeScript": [
        "Define explicit types, avoid 'any' unless necessary",
        "Use interfaces for object shapes",
        "Leverage union types and type guards",
        "Use const/let instead of var",
        "Handle promises properly with async/await",
        "Use strict mode in tsconfig.json",
    ],
    "Go": [
        "Follow Go formatting conventions (gofmt)",
        "Handle errors explicitly, don't ignore them",
        "Use defer for cleanup operations",
        "Use goroutines and channels appropriately",
        "Keep exported names simple and clear",
        "Use context for cancellation and timeouts",
    ],
}

# --------------------------
# Static keyword-based issue detection (language-agnostic)
# --------------------------
STATIC_ISSUES = {
    "TODO": {
        "type": "style",
        "message": "TODO comment found.",
        "suggestion": "Resolve or remove TODOs before merge."
    },
    "FIXME": {
        "type": "style",
        "message": "FIXME comment found.",
        "suggestion": "Address FIXME comments before merge."
    },
    "console.log": {
        "type": "style",
        "message": "Debug console.log detected.",
        "suggestion": "Remove debug console.log or replace with proper logging."
    },
    "System.out.print": {
        "type": "style",
        "message": "Debug System.out.print detected.",
        "suggestion": "Remove debug prints or use a logging framework."
    },
}


def get_file_language(filename: str) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: Language name or "Unknown"
    """
    import os
    _, ext = os.path.splitext(filename.lower())
    return LANGUAGE_MAP.get(ext, "Unknown")


def extract_code_context(patch: str, issue_keywords: list = None) -> dict:
    """
    Extract code snippets with line numbers from a diff patch.
    
    Args:
        patch (str): The diff patch content
        issue_keywords (list): Optional keywords to find relevant sections
        
    Returns:
        dict: Dictionary with line ranges and code snippets
    """
    lines = patch.splitlines()
    code_blocks = []
    current_line = 0
    
    for i, line in enumerate(lines):
        # Parse diff hunk headers like @@ -15,7 +15,8 @@
        if line.startswith("@@"):
            import re
            match = re.search(r'@@ -\d+,?\d* \+(\d+),?(\d*) @@', line)
            if match:
                current_line = int(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            # Added line
            code_line = line[1:]  # Remove the '+'
            code_blocks.append({
                "line_number": current_line,
                "type": "added",
                "code": code_line
            })
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            # Removed line (don't increment line number)
            pass
        elif not line.startswith("\\"):
            # Context line
            current_line += 1
    
    return code_blocks


def group_code_by_context(code_blocks: list, context_lines: int = 3) -> list:
    """
    Group code blocks into continuous sections with context.
    
    Args:
        code_blocks (list): List of code line dicts
        context_lines (int): Number of context lines to include
        
    Returns:
        list: List of grouped code sections
    """
    if not code_blocks:
        return []
    
    sections = []
    current_section = {
        "start_line": code_blocks[0]["line_number"],
        "end_line": code_blocks[0]["line_number"],
        "lines": [code_blocks[0]]
    }
    
    for block in code_blocks[1:]:
        # If within context range, extend current section
        if block["line_number"] - current_section["end_line"] <= context_lines + 1:
            current_section["end_line"] = block["line_number"]
            current_section["lines"].append(block)
        else:
            # Start new section
            sections.append(current_section)
            current_section = {
                "start_line": block["line_number"],
                "end_line": block["line_number"],
                "lines": [block]
            }
    
    # Add the last section
    sections.append(current_section)
    
    return sections


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

        # Skip non-code files (images, binaries, etc.)
        if not patch.strip():
            continue
            
        # Detect language from file extension
        language = get_file_language(filename)
        
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

        # --- LLM-based review for supported languages ---
        if language != "Unknown" and patch.strip():
            # Get language-specific best practices
            best_practices = LANGUAGE_BEST_PRACTICES.get(language, [])
            best_practices_text = "\n".join(f"- {bp}" for bp in best_practices) if best_practices else "Follow general coding standards"

            custom_guidelines_section = ""
            if state.custom_guidelines:
                custom_guidelines_section = f"Additionally, adhere to these custom project guidelines:\n{state.custom_guidelines}"

            full_prompt_content = f"""{SYSTEM_PROMPT_CONTENT}

# Extended Rules and Best Practices:
{EXTENDED_RULES_CONTENT}

# Language-Specific Best Practices for {language}:
{best_practices_text}

{custom_guidelines_section}

Review the provided code patch for the file `{filename}`.
Provide your feedback in a structured JSON array format, where each object represents an issue found. If no issues are found, return an empty JSON array `[]`.

Each issue object should have the following keys:
- `filename`: (string) The name of the file where the issue was found.
- `line_start`: (integer) The starting line number of the issue.
- `line_end`: (integer) The ending line number of the issue.
- `type`: (string) Category of the issue (e.g., "bug", "style", "security", "performance", "maintainability").
- `message`: (string) A concise description of the issue.
- `suggestion`: (string) A clear suggestion for how to fix or improve the code.
- `code_snippet`: (string) The relevant code snippet where the issue is located.

Example of a single issue:
```json
{{
    "filename": "src/main.py",
    "line_start": 10,
    "line_end": 12,
    "type": "style",
    "message": "Variable name 'x' is not descriptive.",
    "suggestion": "Rename 'x' to 'user_count' for better readability.",
    "code_snippet": "x = get_user_count()"
}}
```

Here is the code patch to review:

```diff
{patch}
```
"""

            try:
                response = client.invoke([HumanMessage(content=full_prompt_content)])
                llm_output = response.content
                llm_issues = safe_parse_json(llm_output, filename)
                if isinstance(llm_issues, list):
                    # Enhance issues with code context if not already provided
                    code_blocks = extract_code_context(patch)
                    sections = group_code_by_context(code_blocks)
                    
                    for issue in llm_issues:
                        # If LLM didn't provide code context, add it
                        if "code_snippet" not in issue or not issue["code_snippet"]:
                            # Use the first code section as context
                            if sections:
                                first_section = sections[0]
                                issue["line_start"] = first_section["start_line"]
                                issue["line_end"] = first_section["end_line"]
                                issue["code_snippet"] = "\n".join(
                                    f"{line['code']}" for line in first_section["lines"]
                                )
                        
                        # Ensure line numbers are present
                        if "line_start" not in issue and sections:
                            issue["line_start"] = sections[0]["start_line"]
                        if "line_end" not in issue and sections:
                            issue["line_end"] = sections[0]["end_line"]
                    
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