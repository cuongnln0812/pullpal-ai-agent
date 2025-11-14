# System Patterns: PullPal AI Agent

## Architecture Overview

### Agent Orchestration Pattern
The system uses **LangGraph** for agent orchestration, implementing a sequential workflow:

```
PR Fetcher → Code Review → Test Coverage → Doc Summarizer → END
```

Each agent is a node in a state graph that processes and enriches the shared state.

### State Management Pattern
**Inheritance-based State Evolution**:
- `PRFetcherAgentState`: Base state with PR URL and file data
- `CodeReviewAgentState`: Extends with `findings` list
- `TestCoverageAgentState`: Extends with `coverage_findings` list
- `PRSummaryAgentState`: Extends with `pr_summary` string

State flows through the graph, accumulating data at each stage.

## Key Technical Decisions

### 1. Multi-Agent Architecture
**Decision**: Separate agents for different concerns
**Rationale**: 
- Single Responsibility Principle
- Easy to extend with new agents
- Clear separation of concerns
- Testable in isolation

### 2. LangGraph for Orchestration
**Decision**: Use LangGraph StateGraph instead of manual coordination
**Rationale**:
- Built-in state management
- Visualizable workflow (Mermaid diagrams)
- Easy to modify workflow order
- Handles state passing automatically

### 3. Hybrid Analysis Approach
**Decision**: Combine static keyword checks with LLM analysis
**Rationale**:
- Static checks are fast and reliable for common issues
- LLM provides deeper semantic analysis
- Reduces API costs for obvious issues
- Better coverage of edge cases

### 4. State Inheritance Pattern
**Decision**: Use dataclass inheritance for state evolution
**Rationale**:
- Type safety through inheritance
- Clear state progression
- Easy to understand what data is available at each stage
- Prevents accessing data before it's created

## Component Relationships

### Core Components
1. **github_fetcher.py**: GitHub API interaction layer
   - URL parsing
   - File fetching with pagination
   - File normalization

2. **agent-orchestration.py**: Workflow definition
   - Graph construction
   - Node registration
   - Edge definition
   - Workflow compilation

3. **agents/state.py**: State definitions
   - Base state classes
   - State inheritance hierarchy

4. **agents/pr_fetcher_agent.py**: PR data retrieval
   - URL parsing delegation
   - File fetching
   - State initialization

5. **agents/code_review_agent.py**: Code analysis
   - Static keyword checks
   - LLM-powered review
   - Issue categorization

6. **agents/test_coverage_agent.py**: Test analysis
   - Test file detection
   - Missing test identification
   - Test stub generation

7. **agents/doc_summarizer_agent.py**: Summary generation
   - Statistics collection
   - LLM-powered summarization

8. **ui.py**: Streamlit interface
   - User input handling
   - Workflow invocation
   - Results display

## Critical Implementation Paths

### PR Processing Flow
1. User provides PR URL → `parse_github_pr_url()`
2. Extract owner, repo, PR number
3. Fetch files via GitHub API → `fetch_pr_files()`
4. Normalize file data → `parse_pr_files()`
5. Pass to code review agent
6. Analyze each file (static + LLM)
7. Check test coverage
8. Generate summary
9. Display results in UI

### Error Handling Patterns
- **GitHub API Errors**: Rate limit detection, token validation
- **LLM Errors**: Fallback to static analysis, graceful degradation
- **JSON Parsing**: Safe parsing with fallback extraction
- **Missing Data**: Default to empty lists/None, continue processing

## Design Patterns in Use

### 1. Agent Pattern
Each agent is a function that takes state and returns updated state.

### 2. Pipeline Pattern
Agents form a processing pipeline where output of one feeds into the next.

### 3. Strategy Pattern
Different analysis strategies (static vs LLM) are applied based on file type.

### 4. Template Method Pattern
State classes define structure, agents fill in the data.

## Extension Points

### Adding New Agents
1. Create agent function: `def new_agent(state: StateType) -> StateType`
2. Create/extend state class if needed
3. Add node to graph: `graph.add_node("new_agent", new_agent)`
4. Insert edge in workflow

### Adding New Analysis Types
1. Add to static checks dictionary (code_review_agent.py)
2. Or add LLM prompt section
3. Update issue type categories if needed

### Supporting New Languages
1. Extend file extension checks
2. Add language-specific static checks
3. Update LLM prompts with language context

