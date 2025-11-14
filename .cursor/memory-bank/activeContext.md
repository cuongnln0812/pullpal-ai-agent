# Active Context: PullPal AI Agent

## Current Work Focus

### Project Status
The project is in **active development** with core functionality implemented. The basic agent orchestration workflow is complete and functional.

### Recent Changes
- Core agent architecture established
- LangGraph workflow implemented
- Streamlit UI created
- GitHub API integration complete
- Code review agent with static + LLM analysis
- Test coverage agent with stub generation
- Documentation summarizer agent
- System prompt for the code review agent has been externalized to `config/review_system_prompt.md`
- A global ruleset for reviews has been added in `config/global_review_rules.json`
- UI now supports uploading a project-specific guideline file that is threaded through state and injected into the review prompt

## Next Steps

### Immediate Priorities
1. **Testing**: Add unit tests for agents and utilities
2. **Error Handling**: Improve error messages and recovery
3. **UI Polish**: Fix encoding issues in UI (emojis showing as garbled text)
4. **Documentation**: Expand README with setup and usage instructions (including how to configure global rules, system prompt, and project guideline files)

### Short-term Goals
- Add more static code checks
- Improve LLM prompt engineering for better results
- Add support for more file types
- Implement result caching
- Add export functionality (JSON, markdown)

### Medium-term Goals
- Multi-language support (JavaScript, TypeScript, etc.)
- Parallel agent execution for performance
- Integration with CI/CD pipelines
- Webhook support for automatic reviews
- Review history and analytics

## Active Decisions and Considerations

### Current Architecture Decisions
- **Sequential Processing**: Agents run in sequence (simple but potentially slow)
- **State Inheritance**: Using dataclass inheritance for state evolution
- **Hybrid Analysis**: Static checks + LLM for comprehensive coverage
- **Python-First**: Optimized for Python, extensible to other languages

### Open Questions
1. Should we add parallel processing for multiple files?
2. Should we cache LLM responses for similar code patterns?
3. Should we add a database for review history?
4. Should we support batch PR reviews?

### Technical Debt
- UI has encoding issues (emojis not displaying correctly)
- No comprehensive error handling for all edge cases
- Missing unit tests
- No logging framework (using print statements)
- Hardcoded model name ("gemini-2.0-flash")

## Important Patterns and Preferences

### Code Style
- Use type hints throughout
- Dataclasses for state management
- Clear function docstrings
- Separation of concerns (agents, utilities, UI)

### Naming Conventions
- Agent functions: `{name}_agent(state) -> state`
- State classes: `{Name}AgentState`
- File names: snake_case
- Constants: UPPER_SNAKE_CASE

### Error Handling Philosophy
- Graceful degradation (fallback to static analysis if LLM fails)
- Continue processing other files if one fails
- Clear error messages for users
- Log errors but don't crash the workflow

### LLM Usage Patterns
- Temperature 0 for deterministic outputs
- JSON output requested for structured data
- Fallback parsing for malformed JSON
- Clear, specific prompts with examples

## Learnings and Project Insights

### What Works Well
- LangGraph provides clean workflow definition
- State inheritance makes data flow clear
- Hybrid static + LLM approach catches more issues
- Streamlit makes UI development fast

### Challenges Encountered
- LLM JSON output can be inconsistent (requires safe parsing)
- GitHub API rate limits need careful handling
- Large PRs can be slow to process
- UI encoding issues with special characters

### Key Insights
- Static checks are fast and reliable for common issues
- LLM adds value for complex semantic analysis
- State management is critical for multi-agent systems
- User experience matters: clear error messages and loading indicators

## Current Configuration

### Environment Setup
- Python virtual environment in `venv/`
- Environment variables in `.env` file
- Dependencies in `requirements.txt`

### Active Files
- `agent-orchestration.py`: Main workflow definition
- `ui.py`: Streamlit interface
- `github_fetcher.py`: GitHub API utilities
- `agents/`: Agent implementations
- `agents/state.py`: State definitions

### Workflow Order
1. PR Fetcher → 2. Code Review → 3. Test Coverage → 4. Doc Summarizer

## Notes for Future Sessions
- Check for UI encoding fixes needed
- Consider adding logging framework
- Review LLM prompt effectiveness
- Plan test coverage implementation
- Consider performance optimizations

