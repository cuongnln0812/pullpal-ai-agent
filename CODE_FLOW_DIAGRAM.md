# PullPal AI Agent - Code Flow Diagram

## 📋 Table of Contents
- [High-Level Architecture](#high-level-architecture)
- [Detailed Component Flow](#detailed-component-flow)
- [Agent Pipeline](#agent-pipeline)
- [Data Flow](#data-flow)
- [Class Hierarchy](#class-hierarchy)
- [External Dependencies](#external-dependencies)

---

## 🏗️ High-Level Architecture

```mermaid
graph TB
    User[👤 User] -->|Enters PR URL| UI[🖥️ Streamlit UI]
    UI -->|Invokes| Workflow[🔄 LangGraph Workflow]
    Workflow -->|Sequential Execution| Agents[🤖 Agent Pipeline]
    Agents -->|Results| UI
    UI -->|Displays| Results[📊 Formatted Results]
    
    style UI fill:#e1f5ff
    style Workflow fill:#fff4e6
    style Agents fill:#f3e5f5
```

---

## 🔍 Detailed Component Flow

```mermaid
graph LR
    subgraph "Entry Points"
        UI[ui.py<br/>Streamlit Interface]
        CLI[agent_orchestration.py<br/>CLI Entry]
    end
    
    subgraph "Orchestration Layer"
        Workflow[LangGraph Workflow<br/>StateGraph]
    end
    
    subgraph "Agent Layer"
        A1[PR Fetcher<br/>Agent]
        A2[Code Review<br/>Agent]
        A3[Test Coverage<br/>Agent]
        A4[Doc Summarizer<br/>Agent]
    end
    
    subgraph "Integration Layer"
        GH[github_fetcher.py<br/>GitHub API Client]
        LLM[llm_client.py<br/>LLM Adapter]
    end
    
    subgraph "External Services"
        GitHub[🐙 GitHub API]
        AI[🤖 LLM Service<br/>OpenAI/Gemini]
    end
    
    UI --> Workflow
    CLI --> Workflow
    Workflow --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    
    A1 --> GH
    A2 --> LLM
    A3 --> LLM
    A4 --> LLM
    
    GH --> GitHub
    LLM --> AI
    
    style UI fill:#4fc3f7
    style CLI fill:#4fc3f7
    style Workflow fill:#ffb74d
    style A1 fill:#ba68c8
    style A2 fill:#ba68c8
    style A3 fill:#ba68c8
    style A4 fill:#ba68c8
    style GH fill:#81c784
    style LLM fill:#81c784
```

---

## 🔄 Agent Pipeline

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant WF as LangGraph Workflow
    participant A1 as PR Fetcher Agent
    participant A2 as Code Review Agent
    participant A3 as Test Coverage Agent
    participant A4 as Doc Summarizer Agent
    participant GH as GitHub API
    participant LLM as LLM Client
    
    User->>UI: Enter PR URL + Token
    UI->>WF: workflow.invoke(state)
    
    Note over WF: State: PRFetcherAgentState
    WF->>A1: pr_fetcher_agent(state)
    A1->>GH: fetch_pr_files()
    GH-->>A1: Raw PR files
    A1->>GH: fetch_repo_context()
    GH-->>A1: README, languages, structure
    A1->>A1: parse_pr_files()
    Note over A1: Updates state with:<br/>- owner, repo, pr_number<br/>- parsed files<br/>- repo_context
    
    Note over WF: State: CodeReviewAgentState
    WF->>A2: code_review_agent(state)
    loop For each file
        A2->>A2: get_file_language()
        A2->>A2: extract_code_context()
        A2->>A2: Build prompt with repo context
        A2->>LLM: invoke(prompt)
        LLM-->>A2: JSON issues
        A2->>A2: Parse & enhance issues
    end
    Note over A2: Updates state.findings
    
    Note over WF: State: TestCoverageAgentState
    WF->>A3: test_coverage_agent(state)
    loop For each file
        A3->>A3: get_language_config()
        A3->>A3: extract_added_functions()
        A3->>A3: Check for test files
        alt Missing tests
            A3->>LLM: Generate test stubs
            LLM-->>A3: Test code
        end
    end
    Note over A3: Updates state.coverage_findings
    
    Note over WF: State: PRSummaryAgentState
    WF->>A4: doc_summarizer_agent(state)
    A4->>A4: Count changes & tests
    A4->>LLM: Generate summary
    LLM-->>A4: Natural language summary
    Note over A4: Updates state.pr_summary
    
    WF-->>UI: Final state with all results
    UI->>User: Display formatted results
```

---

## 📊 Data Flow

```mermaid
graph TD
    Start([Start]) --> Input[User Input:<br/>PR URL + Token]
    Input --> State1[PRFetcherAgentState]
    
    State1 --> Fetch[PR Fetcher Agent]
    Fetch --> State2[Enhanced State:<br/>+ owner, repo, pr_number<br/>+ files[]<br/>+ repo_context{}]
    
    State2 --> Review[Code Review Agent]
    Review --> State3[CodeReviewAgentState:<br/>+ findings[]<br/>- type, message, suggestion<br/>- line_start, line_end<br/>- code_snippet]
    
    State3 --> Coverage[Test Coverage Agent]
    Coverage --> State4[TestCoverageAgentState:<br/>+ coverage_findings[]<br/>- filename, issue<br/>- generated_tests[]]
    
    State4 --> Summary[Doc Summarizer Agent]
    Summary --> State5[PRSummaryAgentState:<br/>+ pr_summary]
    
    State5 --> Display[Display in UI]
    Display --> End([End])
    
    style Start fill:#4caf50
    style End fill:#f44336
    style State1 fill:#e3f2fd
    style State2 fill:#e3f2fd
    style State3 fill:#fff3e0
    style State4 fill:#fce4ec
    style State5 fill:#f3e5f5
```

---

## 🏛️ Class Hierarchy

```mermaid
classDiagram
    class PRFetcherAgentState {
        +str pr_url
        +Optional~str~ token
        +Optional~str~ owner
        +Optional~str~ repo
        +Optional~int~ pr_number
        +List~Dict~ files
        +Optional~str~ github_token
        +Optional~Dict~ repo_context
    }
    
    class CodeReviewAgentState {
        +List~Dict~ findings
    }
    
    class TestCoverageAgentState {
        +List~Dict~ coverage_findings
    }
    
    class PRSummaryAgentState {
        +Optional~str~ pr_summary
    }
    
    PRFetcherAgentState <|-- CodeReviewAgentState : inherits
    CodeReviewAgentState <|-- TestCoverageAgentState : inherits
    TestCoverageAgentState <|-- PRSummaryAgentState : inherits
    
    class LLMClient {
        -str api_key
        -str model
        -float temperature
        -Optional~str~ host_url
        -OpenAI _openai_client
        -ChatGoogleGenerativeAI _langchain_client
        +invoke(messages) Response
        -_invoke_openai(contents) Response
    }
    
    class GitHubFetcher {
        +parse_github_pr_url(url) Dict
        +fetch_pr_files(owner, repo, pr_number, token) List
        +fetch_repo_context(owner, repo, token) Dict
        +parse_pr_files(files) List
    }
    
    note for PRFetcherAgentState "Base state with PR info\nand repository context"
    note for CodeReviewAgentState "Adds code review findings\nwith issues per file"
    note for TestCoverageAgentState "Adds test coverage gaps\nand generated test stubs"
    note for PRSummaryAgentState "Final state with\nnatural language summary"
    note for LLMClient "Adapter for OpenAI-compatible\nAPIs or Google Gemini"
```

---

## 🔧 Component Details

### 1️⃣ PR Fetcher Agent (`pr_fetcher_agent.py`)
**Purpose**: Fetch PR files and repository context

```mermaid
flowchart TD
    A[Start] --> B[Parse PR URL]
    B --> C{Token provided?}
    C -->|Yes| D[Use token for API]
    C -->|No| E[Use public API]
    D --> F[Fetch PR Files]
    E --> F
    F --> G[Parse files into<br/>normalized format]
    G --> H[Fetch Repo Context]
    H --> I[Get README]
    H --> J[Get languages]
    H --> K[Get package files]
    H --> L[Get directory structure]
    I --> M[Update State]
    J --> M
    K --> M
    L --> M
    M --> N[Return Enhanced State]
    
    style A fill:#4caf50
    style N fill:#2196f3
```

**Key Functions**:
- `parse_github_pr_url()`: Extract owner, repo, PR number
- `fetch_pr_files()`: Get changed files with retry/backoff
- `fetch_repo_context()`: Get README, languages, dependencies, structure
- `parse_pr_files()`: Normalize file data

---

### 2️⃣ Code Review Agent (`code_review_agent.py`)
**Purpose**: Analyze code changes for issues

```mermaid
flowchart TD
    A[Start] --> B{For each file}
    B --> C[Detect language<br/>from extension]
    C --> D[Run static checks<br/>TODO, FIXME, console.log]
    D --> E{Language supported?}
    E -->|No| B
    E -->|Yes| F[Get language best practices]
    F --> G[Build repo context section]
    G --> H[Extract code context<br/>with line numbers]
    H --> I[Construct LLM prompt]
    I --> J[Invoke LLM]
    J --> K[Parse JSON response]
    K --> L[Enhance with line numbers<br/>and code snippets]
    L --> M[Add to findings]
    M --> B
    B -->|Done| N[Return State with findings]
    
    style A fill:#4caf50
    style N fill:#2196f3
```

**Key Functions**:
- `get_file_language()`: Map extension to language
- `extract_code_context()`: Parse diff for line numbers
- `group_code_by_context()`: Group related code sections
- `safe_parse_json()`: Robust JSON parsing

**Language Support**: Python, Java, JavaScript, TypeScript, Go, Ruby, PHP, C#, Kotlin, Rust, Swift, Scala, C++, C

---

### 3️⃣ Test Coverage Agent (`test_coverage_agent.py`)
**Purpose**: Detect missing tests and generate stubs

```mermaid
flowchart TD
    A[Start] --> B{For each file}
    B --> C[Get language config]
    C --> D{Test file?}
    D -->|Yes| B
    D -->|No| E[Extract added functions<br/>using language patterns]
    E --> F{Functions found?}
    F -->|No| B
    F -->|Yes| G{Test files modified?}
    G -->|Yes| B
    G -->|No| H[Build test generation prompt<br/>with language & framework]
    H --> I[Invoke LLM]
    I --> J[Generate test code]
    J --> K[Add to coverage_findings]
    K --> B
    B -->|Done| L[Return State with coverage findings]
    
    style A fill:#4caf50
    style L fill:#2196f3
```

**Key Functions**:
- `get_language_config()`: Get test framework & patterns
- `extract_added_functions()`: Find new code using regex

**Supported Test Frameworks**: pytest, JUnit 5, Jest, RSpec, PHPUnit, xUnit, Go testing, Rust tests, etc.

---

### 4️⃣ Doc Summarizer Agent (`doc_summarizer_agent.py`)
**Purpose**: Generate natural language PR summary

```mermaid
flowchart TD
    A[Start] --> B[Count file changes<br/>added, modified, removed]
    B --> C[Count new functions/classes]
    C --> D[Count generated tests]
    D --> E[Build statistics prompt]
    E --> F[Invoke LLM]
    F --> G[Get natural language summary]
    G --> H{LLM failed?}
    H -->|Yes| I[Use fallback template]
    H -->|No| J[Update state.pr_summary]
    I --> J
    J --> K[Return Final State]
    
    style A fill:#4caf50
    style K fill:#2196f3
```

---

### 🌐 GitHub Fetcher (`github_fetcher.py`)
**Features**:
- ✅ Rate limit handling with auto-retry
- ✅ Exponential backoff for errors
- ✅ Support for private repos with token
- ✅ Repository context fetching (README, languages, dependencies, structure)
- ✅ Pagination for large PRs

---

### 🤖 LLM Client (`llm_client.py`)
**Features**:
- ✅ Dual-mode: OpenAI-compatible API or Google Gemini
- ✅ Routes based on `HOST_URL` environment variable
- ✅ Unified interface for both backends
- ✅ Graceful error handling

**Decision Logic**:
```
IF HOST_URL is set:
    Use OpenAI SDK with custom base_url
ELSE:
    Use langchain_google_genai.ChatGoogleGenerativeAI
```

---

## 🎨 Streamlit UI Flow

```mermaid
stateDiagram-v2
    [*] --> InputForm: Page Load
    InputForm --> Validation: Click "Start Review"
    Validation --> Processing: Valid URL
    Validation --> InputForm: Invalid URL
    
    Processing --> FetchPR: Invoke Workflow
    FetchPR --> ReviewCode: PR Fetched
    ReviewCode --> CheckTests: Issues Found
    CheckTests --> Summarize: Tests Checked
    Summarize --> DisplayResults: Summary Ready
    
    DisplayResults --> ShowOverview: Render UI
    ShowOverview --> ShowFindings
    ShowFindings --> ShowCoverage
    ShowCoverage --> ShowSummary
    ShowSummary --> [*]
    
    note right of Processing
        Shows spinner:
        "Fetching PR and analyzing..."
    end note
    
    note right of DisplayResults
        Displays:
        - PR Overview (owner, repo, files)
        - Code Review Findings (badges, line numbers)
        - Test Coverage (generated tests)
        - PR Summary
    end note
```

---

## 🔐 Environment Configuration

```mermaid
graph LR
    ENV[.env File] --> API[GOOGLE_API_KEY<br/>sk-... for OpenAI]
    ENV --> MODEL[GOOGLE_MODEL_NAME<br/>Model identifier]
    ENV --> HOST[HOST_URL<br/>Custom API endpoint]
    ENV --> TOKEN[GITHUB_TOKEN<br/>For private repos]
    
    API --> LLM[LLM Client]
    MODEL --> LLM
    HOST --> Decision{HOST_URL set?}
    Decision -->|Yes| OpenAI[Use OpenAI SDK]
    Decision -->|No| Gemini[Use Gemini via langchain]
    
    TOKEN --> GitHub[GitHub API Client]
    
    style ENV fill:#fff3e0
    style LLM fill:#e1bee7
    style GitHub fill:#c5e1a5
```

---

## 📦 External Dependencies

```mermaid
graph TB
    subgraph "Core Dependencies"
        LC[langchain<br/>Agent framework]
        LG[langgraph<br/>State graph orchestration]
        ST[streamlit<br/>Web UI]
    end
    
    subgraph "LLM Providers"
        LCGG[langchain_google_genai<br/>Google Gemini integration]
        OAI[openai<br/>OpenAI SDK]
    end
    
    subgraph "Utilities"
        REQ[requests<br/>HTTP client]
        ENV[python-dotenv<br/>Environment variables]
    end
    
    App[PullPal Agent] --> LC
    App --> LG
    App --> ST
    App --> REQ
    App --> ENV
    
    LLMClient[LLM Client] --> LCGG
    LLMClient --> OAI
    
    style App fill:#2196f3
```

---

## 🎯 Error Handling Strategy

```mermaid
flowchart TD
    A[Operation] --> B{Error Occurred?}
    B -->|No| C[Success]
    B -->|Yes| D{Error Type}
    
    D -->|Rate Limit| E{Wait time?}
    E -->|Short| F[Auto-sleep & retry]
    E -->|Long| G[Surface error to user]
    
    D -->|Network Error| H{Retry count?}
    H -->|< Max| I[Exponential backoff]
    H -->|>= Max| G
    
    D -->|Invalid JSON| J[Extract with regex]
    J --> K{Found?}
    K -->|Yes| C
    K -->|No| L[Return empty array]
    
    D -->|LLM Failure| M[Use fallback template]
    
    F --> A
    I --> A
    
    style C fill:#4caf50
    style G fill:#f44336
    style L fill:#ff9800
    style M fill:#ff9800
```

---

## 📝 Key Design Patterns

### 1. **State Inheritance Chain**
```
PRFetcherAgentState
    ↓ (inherits)
CodeReviewAgentState
    ↓ (inherits)
TestCoverageAgentState
    ↓ (inherits)
PRSummaryAgentState
```
Each agent adds its own fields while maintaining access to all previous data.

### 2. **Adapter Pattern (LLM Client)**
Single interface abstracts multiple LLM backends (OpenAI, Gemini).

### 3. **Pipeline Pattern (LangGraph)**
Sequential execution with state passing between agents.

### 4. **Strategy Pattern (Language Detection)**
Different behavior based on file type detection.

---

## 🚀 Execution Flow Summary

1. **User Input**: Enters PR URL in Streamlit UI
2. **Initialization**: Create initial state with PR URL
3. **PR Fetcher**: Fetch files and repo context from GitHub
4. **Code Review**: Analyze each file with LLM, detect issues
5. **Test Coverage**: Check for missing tests, generate stubs
6. **Summarize**: Create natural language summary
7. **Display**: Render formatted results in UI

---

## 📊 Performance Characteristics

| Component | Bottleneck | Mitigation |
|-----------|-----------|-----------|
| GitHub API | Rate limits (60/hr) | Token auth (5000/hr), auto-retry |
| LLM Calls | Response time | Parallel where possible, streaming |
| Large PRs | Many files | Pagination, selective analysis |
| JSON Parsing | Malformed output | Regex extraction, fallbacks |

---

## 🔮 Future Enhancements (Potential)

```mermaid
mindmap
  root((PullPal<br/>Future))
    Performance
      Caching repo context
      Parallel agent execution
      Streaming LLM responses
    Features
      Multi-PR comparison
      Security scanning
      Automated PR comments
      Custom rule engines
    Integrations
      GitLab support
      Bitbucket support
      Slack notifications
      JIRA linking
    Intelligence
      Learning from past reviews
      Project-specific conventions
      Historical trend analysis
```

---

## 📖 References

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **GitHub REST API**: https://docs.github.com/en/rest
- **OpenAI API**: https://platform.openai.com/docs/api-reference
- **Streamlit Docs**: https://docs.streamlit.io/

---

*Generated: 2025-11-08*  
*Project: PullPal AI Agent*  
*Version: 1.0*
