import re
import os
from dotenv import load_dotenv
from agents.llm_client import get_llm_client
from agents.prompt_loader import load_prompt
from langchain_core.messages import HumanMessage
from agents.state import TestCoverageAgentState, CodeReviewAgentState

load_dotenv()

# --------------------------
# Initialize LLM client (uses HOST_URL if set, otherwise langchain)
# --------------------------
llm = get_llm_client(convert_system_message_to_human=True)

# --------------------------
# Load prompt from file
# --------------------------
PROMPT_TEMPLATE = load_prompt("test_coverage_prompt.txt")

# --------------------------
# Language and testing framework mapping
# --------------------------
LANGUAGE_TEST_CONFIG = {
    ".py": {
        "language": "Python",
        "framework": "pytest",
        "test_pattern": r"(test_|_test)\.py$",
        "test_dir": "tests",
        "test_prefix": "test_",
        "function_patterns": [r"def\s+(\w+)", r"class\s+(\w+)"],
    },
    ".java": {
        "language": "Java",
        "framework": "JUnit 5",
        "test_pattern": r"Test\.java$",
        "test_dir": "src/test/java",
        "test_suffix": "Test",
        "function_patterns": [r"(public|private|protected)\s+\w+\s+(\w+)\s*\(", r"class\s+(\w+)"],
    },
    ".js": {
        "language": "JavaScript",
        "framework": "Jest",
        "test_pattern": r"(\.test\.js|\.spec\.js)$",
        "test_dir": "__tests__",
        "test_suffix": ".test.js",
        "function_patterns": [r"function\s+(\w+)", r"const\s+(\w+)\s*=", r"class\s+(\w+)"],
    },
    ".jsx": {
        "language": "JavaScript (React)",
        "framework": "Jest + React Testing Library",
        "test_pattern": r"(\.test\.jsx|\.spec\.jsx)$",
        "test_dir": "__tests__",
        "test_suffix": ".test.jsx",
        "function_patterns": [r"function\s+(\w+)", r"const\s+(\w+)\s*=", r"class\s+(\w+)"],
    },
    ".ts": {
        "language": "TypeScript",
        "framework": "Jest",
        "test_pattern": r"(\.test\.ts|\.spec\.ts)$",
        "test_dir": "__tests__",
        "test_suffix": ".test.ts",
        "function_patterns": [r"function\s+(\w+)", r"const\s+(\w+)\s*=", r"class\s+(\w+)"],
    },
    ".tsx": {
        "language": "TypeScript (React)",
        "framework": "Jest + React Testing Library",
        "test_pattern": r"(\.test\.tsx|\.spec\.tsx)$",
        "test_dir": "__tests__",
        "test_suffix": ".test.tsx",
        "function_patterns": [r"function\s+(\w+)", r"const\s+(\w+)\s*=", r"class\s+(\w+)"],
    },
    ".go": {
        "language": "Go",
        "framework": "testing package",
        "test_pattern": r"_test\.go$",
        "test_dir": "",
        "test_suffix": "_test.go",
        "function_patterns": [r"func\s+(\w+)", r"type\s+(\w+)\s+struct"],
    },
    ".rs": {
        "language": "Rust",
        "framework": "built-in test framework",
        "test_pattern": r"(tests\.rs|_test\.rs)$",
        "test_dir": "tests",
        "test_suffix": "_test.rs",
        "function_patterns": [r"fn\s+(\w+)", r"struct\s+(\w+)"],
    },
    ".rb": {
        "language": "Ruby",
        "framework": "RSpec",
        "test_pattern": r"_spec\.rb$",
        "test_dir": "spec",
        "test_suffix": "_spec.rb",
        "function_patterns": [r"def\s+(\w+)", r"class\s+(\w+)"],
    },
    ".php": {
        "language": "PHP",
        "framework": "PHPUnit",
        "test_pattern": r"Test\.php$",
        "test_dir": "tests",
        "test_suffix": "Test.php",
        "function_patterns": [r"function\s+(\w+)", r"class\s+(\w+)"],
    },
    ".cs": {
        "language": "C#",
        "framework": "xUnit",
        "test_pattern": r"Tests\.cs$",
        "test_dir": "Tests",
        "test_suffix": "Tests.cs",
        "function_patterns": [r"(public|private|protected)\s+\w+\s+(\w+)\s*\(", r"class\s+(\w+)"],
    },
    ".kt": {
        "language": "Kotlin",
        "framework": "JUnit 5",
        "test_pattern": r"Test\.kt$",
        "test_dir": "src/test/kotlin",
        "test_suffix": "Test.kt",
        "function_patterns": [r"fun\s+(\w+)", r"class\s+(\w+)"],
    },
}


def get_language_config(filename: str):
    """Get language configuration based on file extension."""
    _, ext = os.path.splitext(filename.lower())
    return LANGUAGE_TEST_CONFIG.get(ext, None)


def extract_added_functions(patch: str, config: dict) -> list[str]:
    """
    Extract new functions and classes from a GitHub PR diff based on language patterns.

    Args:
        patch (str): The diff string from a PR file.
        config (dict): Language configuration with function_patterns.

    Returns:
        list[str]: List of added function/class signatures.
    """
    added = []
    if not config:
        return added
        
    patterns = config.get("function_patterns", [])
    
    for line in patch.splitlines():
        if line.startswith("+"):
            clean_line = line[1:].strip()
            for pattern in patterns:
                matches = re.findall(pattern, clean_line)
                if matches:
                    # Handle tuples from multiple capture groups
                    for match in matches:
                        if isinstance(match, tuple):
                            # Take the last non-empty group
                            name = next((m for m in reversed(match) if m), None)
                            if name:
                                added.append(clean_line)
                                break
                        else:
                            added.append(clean_line)
                            break
    return added


def test_coverage_agent(state: TestCoverageAgentState) -> TestCoverageAgentState:
    """
    Test Coverage Agent.

    Detects if new/changed code has corresponding tests.
    Generates language-appropriate test stubs for missing tests.

    Args:
        state (TestCoverageAgentState): Current state with PR files and code review findings.

    Returns:
        TestCoverageAgentState: Updated state with coverage findings.
    """
    findings = []

    # Group files by language to check for test files
    changed_files = [f["filename"] for f in state.files]
    
    for f in state.files:
        filename = f["filename"]
        patch = f.get("patch", "")
        
        # Get language configuration
        config = get_language_config(filename)
        if not config:
            continue  # Skip unsupported file types
        
        # Skip test files themselves
        if re.search(config["test_pattern"], filename):
            continue
        
        # Extract added functions/classes based on language
        added_entities = extract_added_functions(patch, config)
        
        if not added_entities:
            continue
        
        # Check if there are test files for this language
        test_files = [f for f in changed_files if re.search(config["test_pattern"], f)]
        
        # Flag missing tests if there are added functions/classes but no test files modified
        if not test_files:
            language = config["language"]
            framework = config["framework"]
            
            # Determine test file name based on language conventions
            base_name = os.path.basename(filename)
            name_without_ext = os.path.splitext(base_name)[0]
            
            if config.get("test_prefix"):
                test_filename = f"{config['test_dir']}/{config['test_prefix']}{base_name}"
            elif config.get("test_suffix"):
                ext = os.path.splitext(filename)[1]
                if config["test_suffix"].startswith("_") or config["test_suffix"].startswith("."):
                    test_filename = f"{config['test_dir']}/{name_without_ext}{config['test_suffix']}"
                else:
                    test_filename = f"{config['test_dir']}/{name_without_ext}{config['test_suffix']}"
            else:
                test_filename = f"{config['test_dir']}/test_{base_name}"
            
            issue = {
                "filename": filename,
                "issue": "Missing tests",
                "message": f"New functions/classes added in {filename} but no test files were modified.",
                "suggestion": f"Add unit tests using {framework} in {test_filename}",
                "generated_tests": []
            }

            # --- Generate test stubs with LLM ---
            prompt = PROMPT_TEMPLATE.format(
                language=language,
                framework=framework,
                filename=filename,
                added_entities='\n'.join(added_entities)
            )

            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                issue["generated_tests"].append({
                    "filename": test_filename,
                    "code": response.content.strip()
                })
            except Exception as e:
                print(f"❌ Test generation failed for {filename}: {e}")

            findings.append(issue)

    state.coverage_findings = findings
    return state