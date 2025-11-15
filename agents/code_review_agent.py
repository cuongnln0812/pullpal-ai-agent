import json
import os
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv
from agents.llm_client import get_llm_client
from agents.prompt_loader import load_prompt
from langchain_core.messages import HumanMessage
from agents.state import CodeReviewAgentState

# RAG imports
try:
    from agents.rag_retriever import get_rag_retriever
    RAG_ENABLED = True
except ImportError:
    RAG_ENABLED = False
    print("⚠️ RAG dependencies not installed. Install: pip install chromadb sentence-transformers")

load_dotenv()

# --------------------------
# Paths & configuration loading
# --------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
GLOBAL_RULES_PATH = PROMPTS_DIR / "global_review_rules.json"
EXTENDED_RULES_PATH = BASE_DIR / "extended_rules.md"


def _load_global_rules() -> List[Dict[str, Any]]:
    """Load global review rules from JSON file."""
    try:
        with GLOBAL_RULES_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print("⚠️ Failed to parse global_review_rules.json, falling back to empty rules.")
    return []


def _load_extended_rules() -> str:
    """Load extended coding rules and best practices from markdown file."""
    try:
        with EXTENDED_RULES_PATH.open("r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


GLOBAL_RULES = _load_global_rules()
EXTENDED_RULES = _load_extended_rules()


def _format_global_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
    """Format global rules into a human-readable text for the prompt."""
    if not rules:
        return "No specific global rules configured."

    lines: List[str] = ["\n**Global Review Rules:**\n"]
    for rule in rules:
        rule_id = rule.get("id", "R?")
        title = rule.get("title", "").strip()
        severity = rule.get("severity", "").upper()
        description = rule.get("description", "").strip()
        fix = rule.get("fix", "").strip()

        lines.append(f"- **[{rule_id}]** ({severity}) {title}")
        lines.append(f"  - {description}")
        lines.append(f"  - Fix: {fix}")
        lines.append("")
    return "\n".join(lines)


# --------------------------
# Initialize LLM client (uses HOST_URL if set, otherwise langchain)
# --------------------------
client = get_llm_client(convert_system_message_to_human=True)

# Load main prompt template from prompts folder
PROMPT_TEMPLATE = load_prompt("code_review_prompt.txt")

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
            best_practices_text = "\n".join(f"- {bp}" for bp in best_practices) if best_practices else "Follow general coding standards."

            # Get custom guidelines from state if provided
            custom_guidelines = getattr(state, "guideline_text", None) or getattr(state, "custom_guidelines", None)
            custom_guidelines_section = f"\n\n**Custom Project Guidelines:**\n{custom_guidelines}" if custom_guidelines else "\nNo custom guidelines provided."

            # Format global rules and extended rules
            global_rules_text = _format_global_rules_for_prompt(GLOBAL_RULES)
            extended_rules_text = f"\n\n**Extended Best Practices:**\n{EXTENDED_RULES}" if EXTENDED_RULES else ""

            # 🆕 RAG: Retrieve relevant context from vector database
            rag_context = ""
            if RAG_ENABLED:
                try:
                    retriever = get_rag_retriever()
                    project_name = getattr(state, "project_name", None)
                    
                    # Get relevant context based on the code patch
                    context = retriever.get_relevant_context(
                        code_snippet=patch[:500],  # Use first 500 chars for search
                        language=language,
                        project_name=project_name,
                        max_rules=5,
                        max_guidelines=3
                    )
                    
                    # Format context for prompt
                    rag_context = retriever.format_context_for_prompt(context)
                    if rag_context:
                        print(f"  🔍 RAG: Retrieved {len(context.get('rules', []))} rules + {len(context.get('guidelines', []))} guidelines")
                except Exception as e:
                    print(f"  ⚠️ RAG retrieval failed: {e}")

            # Build the complete prompt using the template
            prompt = PROMPT_TEMPLATE.format(
                filename=filename,
                language=language,
                best_practices_text=best_practices_text + extended_rules_text + global_rules_text + ("\n\n" + rag_context if rag_context else ""),
                custom_guidelines_section=custom_guidelines_section,
                patch=patch
            )

            try:
                response = client.invoke([HumanMessage(content=prompt)])
                llm_output = response.content
                llm_issues = safe_parse_json(llm_output, filename)
                if isinstance(llm_issues, list):
                    # Enhance issues with code context if not already provided
                    code_blocks = extract_code_context(patch)
                    sections = group_code_by_context(code_blocks)
                    
                    for issue in llm_issues:
                        # Ensure filename is set
                        if "filename" not in issue:
                            issue["filename"] = filename
                        
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