# Project Brief: PullPal AI Agent

## Overview
PullPal AI Agent is an automated pull request review system that uses AI agents to analyze GitHub PRs, perform code reviews, check test coverage, and generate comprehensive summaries.

## Core Requirements

### Primary Goals
1. **Automated PR Analysis**: Fetch and analyze GitHub pull requests automatically
2. **Code Review**: Identify bugs, security issues, style problems, and performance concerns
3. **Test Coverage Analysis**: Detect missing tests and generate test stubs
4. **PR Summarization**: Generate concise natural language summaries of PR changes

### Key Features
- GitHub PR URL parsing and file fetching
- Multi-agent orchestration using LangGraph
- Static code analysis (keyword-based checks)
- LLM-powered code review using Google Gemini
- Test coverage detection and test stub generation
- Streamlit-based web UI for interactive PR reviews
- Support for private repositories via GitHub tokens

### Success Criteria
- Successfully fetch PR files from GitHub (public and private repos)
- Identify code issues across multiple categories (style, bug, security, performance)
- Detect missing test coverage for new code
- Generate actionable suggestions and test stubs
- Provide clear, concise PR summaries

## Scope
- **In Scope**: Python code review, test coverage analysis, PR summarization, web UI
- **Out of Scope**: Multi-language support (currently Python-focused), CI/CD integration, automated PR comments

## Constraints
- Requires GitHub API access (token for private repos)
- Requires Google API key for Gemini LLM
- Currently optimized for Python codebases
- Rate limits apply to GitHub API calls

