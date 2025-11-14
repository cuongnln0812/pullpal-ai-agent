# Tech Context: PullPal AI Agent

## Technologies Used

### Core Framework
- **LangGraph** (>=0.0.25): Agent orchestration and workflow management
- **LangChain** (>=0.1.0): LLM integration framework
- **LangChain Google GenAI**: Google Gemini integration

### AI/ML
- **Google Gemini 2.0 Flash**: Primary LLM for code review and summarization
- **Temperature**: 0 (deterministic outputs)

### Web Framework
- **Streamlit** (>=1.25.0): Web UI for interactive PR reviews
- **FastAPI** (>=0.95.0): API framework (if needed for future API endpoints)
- **Uvicorn** (>=0.22.0): ASGI server

### Data & Storage
- **ChromaDB** (>=0.4.0): Vector database (for potential future RAG features)

### HTTP & API
- **Requests** (>=2.31.0): HTTP library for GitHub API calls
- **HTTPX** (>=0.26.0): Async HTTP client (for potential async operations)

### Utilities
- **Python-dotenv** (>=1.0.0): Environment variable management
- **Pydantic** (>=1.10.0): Data validation (used via LangChain)
- **Pytest** (>=7.0.0): Testing framework

## Development Setup

### Environment Variables
Required in `.env` file:
- `GOOGLE_API_KEY`: Google Gemini API key
- `GITHUB_TOKEN`: Optional GitHub personal access token (for private repos)

### Virtual Environment
- Python virtual environment in `venv/`
- Activate with: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
- **Streamlit UI**: `streamlit run ui.py`
- **Direct orchestration**: `python agent-orchestration.py`

## Technical Constraints

### API Rate Limits
- **GitHub API**: 60 requests/hour unauthenticated, 5000/hour authenticated
- **Google Gemini**: Subject to API quota limits
- System handles rate limit errors gracefully

### File Size Limitations
- GitHub API may truncate large file patches
- System detects truncated patches via `truncated` flag
- Large files (>200 lines) trigger performance warnings

### Language Support
- Currently optimized for **Python** code
- Static checks are Python-specific
- LLM prompts assume Python context
- Can be extended to other languages

### Token Management
- GitHub token stored in state, not persisted
- Google API key from environment variables
- No token encryption (consider for production)

## Dependencies

### Critical Dependencies
- `langgraph`: Core orchestration (no alternative in current design)
- `langchain-google_genai`: Gemini integration
- `streamlit`: UI framework
- `requests`: GitHub API calls

### Optional Dependencies
- `chromadb`: Not currently used, but included for future features
- `fastapi`/`uvicorn`: Not currently used, reserved for API endpoints

## Tool Usage Patterns

### GitHub API
- Base URL: `https://api.github.com`
- Endpoint: `/repos/{owner}/{repo}/pulls/{pr_number}/files`
- Pagination: 100 files per page
- Authentication: Optional token header

### Google Gemini API
- Model: `gemini-2.0-flash`
- Temperature: 0 (deterministic)
- System message conversion: Enabled for better formatting
- Error handling: Try-catch with fallback to static analysis

### Streamlit
- Page config: Wide layout
- Input: Text input for PR URL and token
- Output: Columns, expanders, code blocks
- State: Session-based (not persistent)

## Development Workflow

### Code Organization
- Root: Main orchestration and UI
- `agents/`: Individual agent implementations
- `agents/state.py`: Shared state definitions
- `github_fetcher.py`: GitHub API utilities

### Testing
- Pytest framework available
- Test files should follow `test_*.py` or `*_test.py` pattern
- No test files currently in codebase

### Error Handling
- GitHub API: Rate limit detection, status code checking
- LLM: Exception catching with fallback
- JSON parsing: Safe parsing with extraction fallback
- User input: URL validation, error messages in UI

## Future Technical Considerations

### Potential Improvements
- Async/await for parallel file processing
- Caching for repeated PR reviews
- Database for storing review history
- Webhook integration for automatic reviews
- Multi-language support expansion
- CI/CD integration
- Vector database for code context (RAG)

### Scalability
- Current design is synchronous (sequential processing)
- Could benefit from parallel agent execution
- Rate limiting may become bottleneck at scale
- Consider queue system for multiple PRs

