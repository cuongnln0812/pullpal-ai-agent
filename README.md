# PullPal AI Agent 🤖

An intelligent AI-powered agent for automated pull request code review, test coverage analysis, and documentation generation. Supports 12+ programming languages with language-specific best practices.

## Features ✨

- 🔍 **Multi-Language Code Review**: Automated code analysis for Python, Java, JavaScript, TypeScript, Go, Ruby, PHP, C#, Kotlin, and more
- 🧪 **Test Coverage Analysis**: Detects missing tests and generates language-appropriate test stubs
- 📊 **Smart PR Summarization**: AI-generated natural language summaries of pull request changes
- 🎯 **Language-Specific Best Practices**: Applies framework and language-specific coding standards
- 📍 **GitHub-Style Comments**: Shows exact line numbers and code snippets like GitHub code reviews
- 🌐 **Custom LLM Support**: Works with OpenAI-compatible endpoints or Google Gemini

## Supported Languages

| Language | Testing Framework | Best Practices |
|----------|------------------|----------------|
| Python | pytest | PEP 8, type hints, context managers |
| Java | JUnit 5 | SOLID principles, try-with-resources, Optional |
| JavaScript | Jest | const/let, async/await, === comparisons |
| TypeScript | Jest | Type safety, interfaces, strict mode |
| Go | testing package | Error handling, goroutines, defer |
| Ruby | RSpec | Ruby conventions |
| PHP | PHPUnit | PSR standards |
| C# | xUnit | .NET best practices |
| Kotlin | JUnit 5 | Kotlin idioms |
| And more... | | |

## Prerequisites 📋

- Python 3.9 or higher
- Git
- GitHub account (for PR access)
- LLM API access (Google AI Studio or OpenAI-compatible endpoint)

## Installation & Setup 🚀

### 1. Clone the Repository

```powershell
git clone https://github.com/cuongnln0812/pullpal-ai-agent.git
cd pullpal-ai-agent
```

### 2. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration
GOOGLE_API_KEY=your_api_key_here
GOOGLE_MODEL_NAME=gemini-2.5-flash
HOST_URL=https://your-llm-endpoint.com/use

# GitHub Access (Optional but recommended)
GITHUB_TOKEN=ghp_your_github_token_here
```

**Getting API Keys:**

- **Google AI Studio**: Get your API key at [ai.google.dev](https://ai.google.dev/)
- **OpenAI-Compatible Host**: Use your custom endpoint URL in `HOST_URL`
- **GitHub Token**: Create at [github.com/settings/tokens](https://github.com/settings/tokens)
  - Required scopes: `repo` (for private repos) or `public_repo` (for public repos)
  - Without a token: 60 requests/hour limit
  - With a token: 5,000 requests/hour

### 5. Verify Installation

```powershell
python -c "from agents.llm_client import get_llm_client; print('✓ Installation successful')"
```

## Running the Application 🎯

### Start the Streamlit UI

```powershell
streamlit run .\ui.py
```

The app will automatically open in your default browser at `http://localhost:8501`

## Usage Guide 📖

### Step 1: Enter Pull Request URL

1. Copy the URL of any GitHub pull request you want to review
   - Example: `https://github.com/owner/repo/pull/123`
   - Works with both public and private repositories (with proper token)

2. Paste it in the **"Enter GitHub PR URL"** field

### Step 2: Add GitHub Token (Optional)

- If reviewing a **private repository**, enter your GitHub Personal Access Token
- For **public repositories**, the token is optional but recommended to avoid rate limits
- The token is used only for this session and is not stored

### Step 2b: (Optional) Upload Project Coding Guidelines

You can provide **project-specific coding rules** for the reviewer:

- In the UI, use the **"Upload project coding guideline / rules (optional, .md, .txt, .json)"** uploader.
- Supported formats: `.md`, `.txt`, `.json`.
- This content is passed to the LLM together with the global rules and language best practices, so findings will be aligned with your team’s conventions.

Example guideline content (JSON):

```json
[
  {
    "id": "R6",
    "title": "LLM providers must not create clients directly",
    "severity": "error",
    "scope": "internal/providers/llm/**",
    "description": "LLM providers should not construct their own HTTP or API clients.",
    "fix": "Request the client from the dependency injection system instead of creating it directly."
  }
]
```

Or you can upload a Markdown/text file describing anti‑patterns, Sonar rules, and team conventions in free-form prose.

### Step 3: Start Review

Click the **"🚀 Start PR Review"** button and wait while the agent:

1. **Fetches PR files** from GitHub
2. **Analyzes code** for bugs, security issues, performance problems, and style violations
3. **Checks test coverage** and generates missing test stubs
4. **Summarizes changes** in natural language

### Step 4: Review Results

The UI displays three main sections:

#### 📄 PR Overview

- Repository owner and name
- PR number
- Total files changed

#### 📝 Code Review Findings

- **Visual badges**: 🐛 Bugs, 🔒 Security, ⚡ Performance, 💅 Style
- **Line numbers**: Exact location of each issue (e.g., "📍 Lines 42-48")
- **Code snippets**: Syntax-highlighted code showing the problem
- **Suggestions**: Actionable recommendations to fix each issue

Example:

```text
🐛 Issue #1: BUG
📍 Lines 45-48

Code:
public User getUser(Long id) {
    return userRepository.findById(id).get();
}

Issue: Calling .get() without checking if Optional is present

💡 Suggestion: Use .orElseThrow() or check if Optional is present
```

#### 🧪 Test Coverage Findings

- Detects missing tests for new functions/classes
- Generates language-appropriate test stubs
- Shows test file location and framework (e.g., JUnit 5, pytest, Jest)

#### 🖊 PR Summary

- AI-generated natural language summary
- Highlights key changes, additions, and modifications

## Configuration Options ⚙️

### Custom LLM Endpoint

If using an OpenAI-compatible endpoint:

```bash
HOST_URL=https://your-endpoint.com/api
GOOGLE_API_KEY=sk-your-key-here
GOOGLE_MODEL_NAME=Gemini-2.5-Flash
```

The agent will use the OpenAI SDK with your custom `base_url`.

### Rate Limit Auto-Wait

Control automatic waiting for GitHub rate limits:

```bash
GITHUB_MAX_AUTO_WAIT=300  # Max seconds to auto-wait (default: 300)
```

### Custom Review Rules & System Prompt

The reviewer’s system prompt and global rules are **externalized into config files** so you can customize them without changing Python code:

- `config/review_system_prompt.md`  
  - Base **system prompt template** for the code review agent.  
  - Placeholders:
    - `{language}` – detected from the file extension (Python, Java, etc.).
    - `{global_rules}` – rendered from the global rules JSON below.
    - `{best_practices}` – built-in language-specific best practices.
    - `{project_guidelines}` – content from the guideline file you upload in the UI.
  - Edit this file to change tone, constraints, or the structure of the expected JSON output.

- `config/global_review_rules.json`  
  - Shared **global ruleset** applied to every PR (e.g. anti‑patterns, Sonar rules, architecture constraints).  
  - Each rule object has:
    - `id`, `title`, `severity`, `scope`, `description`, `fix`.
  - Add, remove, or tweak rules here; they will automatically be injected into the reviewer’s system prompt.

At runtime, the code review agent evaluates each file using:

1. Global rules from `config/global_review_rules.json`  
2. Language best practices (built-in)  
3. The per-PR guideline file you upload in the UI  
4. The system prompt template in `config/review_system_prompt.md`

## Troubleshooting 🔧

### "GitHub API rate limit exceeded"

- **Solution**: Add a `GITHUB_TOKEN` to your `.env` file
- Without token: 60 requests/hour
- With token: 5,000 requests/hour

### "API key not valid"

- **Check**: Ensure `GOOGLE_API_KEY` in `.env` is correct
- For custom endpoints: Verify `HOST_URL` is reachable
- For Google AI: Get a valid key from [ai.google.dev](https://ai.google.dev/)

### "Cannot import module"

- **Solution**: Ensure virtual environment is activated
- Run: `pip install -r requirements.txt` again

### Import errors or dependency issues

```powershell
# Reinstall dependencies
.\.venv\Scripts\Activate.ps1
pip install --upgrade -r requirements.txt
```

## Project Structure 📁

```text
pullpal-ai-agent/
├── agents/
│   ├── code_review_agent.py      # Multi-language code review
│   ├── test_coverage_agent.py    # Test detection & generation
│   ├── doc_summarizer_agent.py   # PR summarization
│   ├── pr_fetcher_agent.py       # GitHub API integration
│   ├── llm_client.py             # LLM adapter (OpenAI/Gemini)
│   ├── compat.py                 # Compatibility shim
│   └── state.py                  # Agent state dataclasses
├── config/
│   ├── review_system_prompt.md   # System prompt template for reviewer
│   └── global_review_rules.json  # Global review rules (anti-patterns, Sonar-style rules, etc.)
├── ui.py                         # Streamlit UI
├── agent_orchestration.py        # Workflow orchestration
├── github_fetcher.py             # GitHub API utilities
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (create this)
└── README.md                     # This file
```

## Contributing 🤝

Contributions are welcome! Please feel free to submit issues or pull requests.

## License 📄

This project is open source and available under the MIT License.

## Support 💬

If you encounter any issues or have questions:

1. Check the Troubleshooting section above
2. Review the `.env` configuration
3. Open an issue on GitHub

---

Made with ❤️ for better code reviews
