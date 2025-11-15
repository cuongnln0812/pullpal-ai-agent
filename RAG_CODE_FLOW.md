# RAG Code Flow Documentation

## Overview
This document explains the complete data flow from when a user uploads a guideline file in the Streamlit UI to when that knowledge is retrieved from the vector database and used by the LLM for code review.

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    User uploads guideline file (.md/.txt/.json)
                    User enters PR URL (e.g., github.com/owner/repo/pull/123)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         UI.PY (Streamlit)                                │
│  Location: ui.py (lines 29-77)                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        Parse PR URL                    Read Guideline File
     parse_github_pr_url()              guideline_file.getvalue()
     Returns:                           Decode to UTF-8 string
     - owner: "cuongnln0812"                │
     - repo: "pullpal-ai-agent"             │
     - pr_number: 123                       │
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    Create project_name = "owner/repo"
                    e.g., "cuongnln0812/pullpal-ai-agent"
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VECTOR STORE - STORAGE                                │
│  Location: agents/vector_store.py                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                store_project_guidelines(content, filename, project_name)
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            Extract Owner           Chunk Text Content
            from project_name       _chunk_text(content, chunk_size=500)
            "cuongnln0812"          Splits by paragraphs (\\n\\n)
                    │                       │
                    │               Chunks Example:
                    │               - Chunk 0: "Use type hints..." (450 chars)
                    │               - Chunk 1: "Follow PEP 8..." (380 chars)
                    │               - Chunk 2: "Handle errors..." (420 chars)
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    Build Metadata for each chunk
                    {
                      "filename": "coding_guidelines.md",
                      "project": "cuongnln0812/pullpal-ai-agent",
                      "owner": "cuongnln0812",
                      "chunk_index": 0,
                      "source": "user_guideline",
                      "type": "project_guideline"
                    }
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EMBEDDING GENERATION                                  │
│  Model: sentence-transformers/all-MiniLM-L6-v2                          │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                generate_embeddings(chunks)
                                │
            For each chunk text, create 384-dimensional vector
                                │
            Example:
            "Use type hints for all functions" →
            [0.123, -0.456, 0.789, ..., 0.234]  (384 floats)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHROMADB STORAGE                                      │
│  Location: ./chroma_db/                                                 │
│  Collection: project_guidelines                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        guidelines_collection.upsert(
            embeddings=[vector1, vector2, vector3, ...],
            documents=["chunk1", "chunk2", "chunk3", ...],
            metadatas=[meta1, meta2, meta3, ...],
            ids=["owner_repo_file_0", "owner_repo_file_1", ...]
        )
                                │
                    ✅ STORAGE COMPLETE
                                │
                                │
═══════════════════════════════════════════════════════════════════════════
                                │
                    USER STARTS CODE REVIEW
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW ORCHESTRATION                                │
│  Location: agent_orchestration.py                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        workflow.invoke(state)
                                │
        Execution Flow:
        1. pr_fetcher_agent → Fetch PR files from GitHub
        2. code_review_agent → Review code (RAG USED HERE)
        3. test_coverage_agent → Check test coverage
        4. doc_summarizer_agent → Generate summary
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CODE REVIEW AGENT (RAG RETRIEVAL)                     │
│  Location: agents/code_review_agent.py (lines 306-365)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        For each file in PR:
            1. Detect language (Python, Java, JS, etc.)
            2. Extract code patch from PR diff
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RAG RETRIEVER - QUERY BUILDING                        │
│  Location: agents/rag_retriever.py                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        retriever = get_rag_retriever()
        project_name = state.project_name  # "owner/repo"
                                │
        Build search query:
        query = f"{language} code review: {patch[:500]}"
        Example: "Python code review: def process_data(df): ..."
                                │
        retriever.get_relevant_context(
            code_snippet=patch[:500],
            language="Python",
            project_name="cuongnln0812/pullpal-ai-agent",
            max_rules=5,
            max_guidelines=3
        )
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
        Search Review Rules         Search Project Guidelines
        (Global best practices)     (User-uploaded docs)
                    │                       │
                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    VECTOR SIMILARITY SEARCH                              │
│  ChromaDB Collections:                                                  │
│  - review_rules (global coding standards)                               │
│  - project_guidelines (user-uploaded guidelines)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        Step 1: Convert query to embedding
        query_embedding = encoder.encode(query)
        → [0.234, -0.567, 0.891, ..., 0.123]  (384 floats)
                                │
        Step 2: Search in review_rules collection
        results = rules_collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        Returns top 5 most similar rules based on cosine similarity
                                │
        Example Results:
        - Rule 1: "Use type hints" (distance: 0.23)
        - Rule 2: "Handle exceptions" (distance: 0.34)
        - Rule 3: "Avoid global variables" (distance: 0.45)
                                │
                                ▼
        Step 3: Search in project_guidelines collection
        results = guidelines_collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            where={"project": "cuongnln0812/pullpal-ai-agent"}  ← FILTER BY PROJECT
        )
        Returns top 3 most similar guideline chunks for THIS PROJECT
                                │
        Example Results:
        - Chunk 0: "Our Python code must use..." (distance: 0.19)
        - Chunk 1: "Error handling should follow..." (distance: 0.28)
        - Chunk 2: "Database queries must be..." (distance: 0.37)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FORMAT CONTEXT FOR LLM                                │
│  Location: agents/rag_retriever.py (format_context_for_prompt)          │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        Format retrieved context into readable text:
                                │
        Output:
        ┌─────────────────────────────────────────────┐
        │ ## 📋 Relevant Review Rules (from RAG):     │
        │                                             │
        │ 1. **[R001]** (HIGH) Use Type Hints        │
        │    All function parameters and returns     │
        │    must have type annotations...           │
        │                                             │
        │ 2. **[R005]** (MEDIUM) Handle Exceptions   │
        │    Use specific exception types...         │
        │                                             │
        │ ## 📖 Relevant Project Guidelines (RAG):    │
        │                                             │
        │ 1. From `coding_guidelines.md`:            │
        │    Our Python code must use type hints...  │
        │                                             │
        │ 2. From `coding_guidelines.md`:            │
        │    Error handling should follow our...     │
        └─────────────────────────────────────────────┘
                                │
                    ✅ RAG CONTEXT READY
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BUILD COMPLETE LLM PROMPT                             │
│  Location: agents/code_review_agent.py (lines 340-365)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        Combine all context:
        1. Template from prompts/code_review_prompt.txt
        2. Language-specific best practices
        3. Global review rules (JSON)
        4. Extended rules (markdown)
        5. 🆕 RAG-retrieved context (rules + guidelines)
        6. Custom guidelines (if provided inline)
        7. Code patch from PR
                                │
        Final Prompt Structure:
        ┌─────────────────────────────────────────────┐
        │ You are a code reviewer. Review this code: │
        │                                             │
        │ **Language:** Python                        │
        │                                             │
        │ **Best Practices:**                         │
        │ - Follow PEP 8                             │
        │ - Use type hints                           │
        │ ...                                        │
        │                                             │
        │ **Global Rules:**                           │
        │ - [R001] Use Type Hints                    │
        │ - [R002] Handle Errors                     │
        │ ...                                        │
        │                                             │
        │ 🆕 **RAG Retrieved Context:**              │
        │ [Formatted rules + guidelines from DB]     │
        │                                             │
        │ **Code to Review:**                         │
        │ ```python                                  │
        │ def process_data(df):                      │
        │     result = df.filter(...)                │
        │ ```                                        │
        │                                             │
        │ Return JSON array of issues...             │
        └─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SEND TO LLM (OpenAI/Anthropic)                        │
│  Location: agents/llm_client.py                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        response = client.invoke([HumanMessage(content=prompt)])
                                │
        LLM processes:
        - Code patch
        - All best practices
        - RAG-retrieved relevant rules/guidelines
        - Project context
                                │
                                ▼
        LLM returns JSON:
        [
          {
            "type": "bug",
            "message": "Missing type hint for parameter 'df'",
            "suggestion": "Add type hint: def process_data(df: pd.DataFrame)",
            "line_start": 5,
            "code_snippet": "def process_data(df):"
          },
          {
            "type": "style",
            "message": "Function lacks docstring",
            "suggestion": "Add docstring explaining parameters and return",
            "line_start": 5
          }
        ]
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARSE & ENHANCE LLM RESPONSE                          │
│  Location: agents/code_review_agent.py (safe_parse_json)                │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        1. Parse JSON response
        2. Extract code context from patch
        3. Add line numbers if missing
        4. Add code snippets if missing
        5. Group issues by file
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    UPDATE STATE WITH FINDINGS                            │
│  Location: agents/code_review_agent.py (return statement)               │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        state.findings = [
          {
            "filename": "src/data_processor.py",
            "issues": [
              {
                "type": "bug",
                "message": "Missing type hint...",
                "suggestion": "Add type hint...",
                "line_start": 5,
                "code_snippet": "def process_data(df):"
              }
            ]
          }
        ]
                                │
                    Return state to workflow
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW CONTINUES                                    │
│  Next Steps: test_coverage_agent → doc_summarizer_agent                │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISPLAY RESULTS IN UI                                 │
│  Location: ui.py (lines 95-150)                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                │
        Show findings with:
        - File name
        - Issue type (bug/security/performance/style)
        - Line numbers
        - Code snippets
        - Issue message
        - Suggestions (influenced by RAG context!)
                                │
                    ✅ REVIEW COMPLETE

```

---

## 📋 Detailed Step-by-Step Flow

### Phase 1: File Upload & Storage

#### Step 1: User Input (ui.py lines 29-32)
```python
guideline_file = st.file_uploader(
    "Upload project coding guideline / rules (optional, .md, .txt, .json)",
    type=["md", "txt", "json"]
)
```
- **Input**: User selects a file from their computer
- **Supported formats**: Markdown (.md), text (.txt), JSON (.json)
- **Example file**: `coding_guidelines.md`

#### Step 2: Parse PR URL (ui.py lines 40-46)
```python
pr_info = parse_github_pr_url(pr_url)
# Returns: {"owner": "cuongnln0812", "repo": "pullpal-ai-agent", "pr_number": 123}

project_name = f"{pr_info['owner']}/{pr_info['repo']}"
# Result: "cuongnln0812/pullpal-ai-agent"
```
- **Purpose**: Extract owner and repo name to identify the project
- **Format**: `"owner/repo"` ensures unique project identification

#### Step 3: Read File Content (ui.py lines 48-51)
```python
guideline_bytes = guideline_file.getvalue()
guideline_content = guideline_bytes.decode("utf-8", errors="ignore")
```
- **Action**: Read binary file data and convert to UTF-8 text
- **Error handling**: Ignores invalid UTF-8 characters

#### Step 4: Store in Vector Database (ui.py lines 55-62)
```python
from agents.vector_store import get_vector_store
vector_store = get_vector_store()

vector_store.store_project_guidelines(
    content=guideline_content,
    filename=guideline_file.name,
    project_name=f"{pr_info['owner']}/{pr_info['repo']}"
)
```
- **Singleton pattern**: `get_vector_store()` returns same instance
- **Parameters**:
  - `content`: Full text of the guideline file
  - `filename`: Original filename (e.g., "coding_guidelines.md")
  - `project_name`: Full project path (e.g., "cuongnln0812/pullpal-ai-agent")

---

### Phase 2: Text Chunking & Embedding

#### Step 5: Extract Owner (vector_store.py lines 127-130)
```python
owner = None
if "/" in project_name:
    parts = project_name.split("/", 1)
    owner = parts[0]  # "cuongnln0812"
```
- **Purpose**: Extract GitHub username for flexible filtering
- **Result**: Owner stored separately from project name

#### Step 6: Chunk Text (vector_store.py lines 133, 249-276)
```python
chunks = self._chunk_text(content, chunk_size=500)

def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
    paragraphs = text.split('\n\n')  # Split by double newlines
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
```

**Example**:
Input file (1500 chars):
```
# Python Coding Guidelines

## Type Hints
All functions must have type hints for parameters and return values.
This improves code readability and catches type errors early.
[... 450 characters ...]

## Error Handling
Always use specific exception types instead of bare except.
Log errors appropriately using the logging module.
[... 380 characters ...]

## Database Access
All database queries must use parameterized statements.
Never concatenate user input into SQL strings.
[... 420 characters ...]
```

Output chunks:
```python
[
    "# Python Coding Guidelines\n\n## Type Hints\nAll functions must...",  # 450 chars
    "## Error Handling\nAlways use specific exception types...",            # 380 chars
    "## Database Access\nAll database queries must use..."                  # 420 chars
]
```

#### Step 7: Build Metadata (vector_store.py lines 135-154)
```python
for idx, chunk in enumerate(chunks):
    metadata = {
        "filename": filename,              # "coding_guidelines.md"
        "project": project_name,           # "cuongnln0812/pullpal-ai-agent"
        "chunk_index": idx,                # 0, 1, 2, ...
        "source": "user_guideline",        # Identifies source type
        "type": "project_guideline"        # Collection type
    }
    if owner:
        metadata["owner"] = owner          # "cuongnln0812"
    
    metadatas.append(metadata)
    
    # Sanitize ID (replace "/" with "_")
    safe_project_name = project_name.replace("/", "_")
    ids.append(f"{safe_project_name}_{filename}_{idx}")
```

**Result**:
```python
metadatas = [
    {
        "filename": "coding_guidelines.md",
        "project": "cuongnln0812/pullpal-ai-agent",
        "owner": "cuongnln0812",
        "chunk_index": 0,
        "source": "user_guideline",
        "type": "project_guideline"
    },
    # ... more chunks
]

ids = [
    "cuongnln0812_pullpal-ai-agent_coding_guidelines.md_0",
    "cuongnln0812_pullpal-ai-agent_coding_guidelines.md_1",
    "cuongnln0812_pullpal-ai-agent_coding_guidelines.md_2"
]
```

#### Step 8: Generate Embeddings (vector_store.py lines 60-68, 163)
```python
embeddings = self.generate_embeddings(documents)

def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
    embeddings = self.encoder.encode(texts, show_progress_bar=False)
    return embeddings.tolist()
```

**Technical Details**:
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Input**: List of text chunks
- **Output**: List of 384-dimensional vectors
- **Process**: 
  1. Tokenize text (split into words/subwords)
  2. Pass through transformer neural network
  3. Pool token embeddings into single sentence embedding
  4. Normalize to unit length

**Example**:
```python
Input:  "All functions must have type hints for parameters and return values"
Output: [0.123, -0.456, 0.789, 0.234, -0.567, ..., 0.891]  # 384 floats

Semantic meaning encoded in vector space:
- Similar concepts have similar vectors (high cosine similarity)
- "type hints" and "type annotations" → close vectors
- "type hints" and "database queries" → distant vectors
```

#### Step 9: Store in ChromaDB (vector_store.py lines 165-171)
```python
self.guidelines_collection.upsert(
    embeddings=embeddings,      # List of 384-dim vectors
    documents=documents,         # Original text chunks
    metadatas=metadatas,        # Project/file/owner info
    ids=ids                      # Unique identifiers
)
```

**ChromaDB Storage Structure**:
```
./chroma_db/
├── chroma.sqlite3           # SQLite database with metadata
└── [collection data]        # Vector indices and embeddings

Collection: project_guidelines
┌──────────────────────────────────────────────────────────────────┐
│ ID: cuongnln0812_pullpal-ai-agent_coding_guidelines.md_0        │
│ Embedding: [0.123, -0.456, ..., 0.891]  (384 floats)           │
│ Document: "# Python Coding Guidelines\n\n## Type Hints..."     │
│ Metadata: {                                                      │
│   "filename": "coding_guidelines.md",                           │
│   "project": "cuongnln0812/pullpal-ai-agent",                  │
│   "owner": "cuongnln0812",                                      │
│   "chunk_index": 0                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
```

✅ **Storage Complete**: Guidelines are now searchable by semantic similarity

---

### Phase 3: Code Review & RAG Retrieval

#### Step 10: Workflow Invocation (agent_orchestration.py lines 16-21)
```python
workflow.invoke(state)

# Workflow execution order:
# 1. pr_fetcher_agent    → Fetch PR files from GitHub API
# 2. code_review_agent   → Review code with RAG ← WE ARE HERE
# 3. test_coverage_agent → Check test coverage
# 4. doc_summarizer_agent → Generate PR summary
```

#### Step 11: Code Review Agent Initialization (code_review_agent.py lines 289-320)
```python
def code_review_agent(state: CodeReviewAgentState) -> CodeReviewAgentState:
    findings = []
    
    for f in state.files:  # Each file changed in PR
        filename = f["filename"]        # e.g., "src/data_processor.py"
        patch = f.get("patch", "")      # Git diff content
        
        # Detect language
        language = get_file_language(filename)  # "Python"
```

**PR File Structure**:
```python
state.files = [
    {
        "filename": "src/data_processor.py",
        "status": "modified",
        "additions": 15,
        "deletions": 3,
        "patch": """
@@ -15,7 +15,8 @@ import pandas as pd
 
-def process_data(df):
+def process_data(df: pd.DataFrame) -> pd.DataFrame:
+    \"\"\"Process dataframe and return cleaned version.\"\"\"
     result = df.filter(...)
     return result
"""
    }
]
```

#### Step 12: RAG Context Retrieval (code_review_agent.py lines 306-342)
```python
if RAG_ENABLED:
    retriever = get_rag_retriever()
    project_name = getattr(state, "project_name", None)  # "owner/repo"
    
    # Get relevant context
    context = retriever.get_relevant_context(
        code_snippet=patch[:500],    # First 500 chars of code
        language=language,           # "Python"
        project_name=project_name,   # "cuongnln0812/pullpal-ai-agent"
        max_rules=5,                 # Top 5 global rules
        max_guidelines=3             # Top 3 project guidelines
    )
    
    # Format for prompt
    rag_context = retriever.format_context_for_prompt(context)
```

#### Step 13: Build Search Query (rag_retriever.py lines 18-37)
```python
def get_relevant_context(self, code_snippet: str, language: str, 
                        project_name: Optional[str] = None,
                        max_rules: int = 5,
                        max_guidelines: int = 3) -> Dict[str, Any]:
    
    # Build search query combining code and language
    query = f"{language} code review: {code_snippet}"
```

**Example Query**:
```python
query = """Python code review: @@ -15,7 +15,8 @@ import pandas as pd

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Process dataframe and return cleaned version.\"\"\"
    result = df.filter(lambda x: x['status'] == 'active')
    return result"""
```

#### Step 14: Vector Similarity Search (rag_retriever.py lines 28-46)

**Part A: Search Review Rules**
```python
relevant_rules = self.vector_store.search_relevant_rules(
    query=query,
    n_results=5
)
```

**Implementation** (vector_store.py lines 173-200):
```python
def search_relevant_rules(self, query: str, n_results: int = 5):
    # Convert query to embedding vector
    query_embedding = self.generate_embeddings([query])[0]
    # Result: [0.234, -0.567, 0.891, ..., 0.123]  (384 floats)
    
    # Search ChromaDB
    results = self.rules_collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
```

**ChromaDB Search Process**:
1. **Calculate cosine similarity** between query vector and all stored rule vectors
2. **Rank by similarity** (lower distance = more similar)
3. **Return top 5** most relevant rules

**Example Results**:
```python
relevant_rules = [
    {
        "content": "Use type hints. All function parameters and return values...",
        "metadata": {
            "rule_id": "R001",
            "title": "Type Hints Required",
            "severity": "high"
        },
        "distance": 0.19  ← Very similar to query!
    },
    {
        "content": "Add docstrings. All functions must have docstrings...",
        "metadata": {"rule_id": "R003", "severity": "medium"},
        "distance": 0.28
    },
    {
        "content": "Handle exceptions. Use specific exception types...",
        "metadata": {"rule_id": "R005", "severity": "high"},
        "distance": 0.45
    }
]
```

**Part B: Search Project Guidelines**
```python
relevant_guidelines = self.vector_store.search_project_guidelines(
    query=query,
    project_name=project_name,  # "cuongnln0812/pullpal-ai-agent"
    n_results=3
)
```

**Implementation** (vector_store.py lines 202-237):
```python
def search_project_guidelines(self, query: str, project_name: Optional[str] = None,
                              owner: Optional[str] = None, n_results: int = 3):
    query_embedding = self.generate_embeddings([query])[0]
    
    # Build filter
    where = None
    if project_name:
        where = {"project": project_name}  ← Filter by exact project match
    
    # Search with filter
    results = self.guidelines_collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where=where  # Only return guidelines for THIS project
    )
```

**Key Feature**: Project filtering ensures each project's guidelines are isolated
- Project A uploads "Use tabs for indentation"
- Project B uploads "Use spaces for indentation"
- Each project only sees their own guidelines ✅

**Example Results**:
```python
relevant_guidelines = [
    {
        "content": "Our Python code must use type hints for all...",
        "metadata": {
            "filename": "coding_guidelines.md",
            "project": "cuongnln0812/pullpal-ai-agent",
            "owner": "cuongnln0812",
            "chunk_index": 0
        },
        "distance": 0.15  ← Highly relevant!
    },
    {
        "content": "DataFrame processing should always validate input...",
        "metadata": {"filename": "coding_guidelines.md", "chunk_index": 2},
        "distance": 0.23
    }
]
```

#### Step 15: Format Context for LLM (rag_retriever.py lines 52-82)
```python
def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
    sections = []
    
    # Format relevant rules
    if context.get("rules"):
        sections.append("## 📋 Relevant Review Rules (from RAG):\n")
        for i, rule in enumerate(context["rules"], 1):
            meta = rule["metadata"]
            sections.append(
                f"{i}. **[{meta.get('rule_id', 'R?')}]** ({meta.get('severity', 'info').upper()}) "
                f"{meta.get('title', 'Rule')}\n"
                f"   {rule['content']}\n"
            )
    
    # Format relevant guidelines
    if context.get("guidelines"):
        sections.append("\n## 📖 Relevant Project Guidelines (from RAG):\n")
        for i, guideline in enumerate(context["guidelines"], 1):
            meta = guideline["metadata"]
            sections.append(
                f"{i}. From `{meta.get('filename', 'unknown')}` "
                f"(project: {meta.get('project', 'unknown')}):\n"
                f"   {guideline['content'][:300]}{'...' if len(guideline['content']) > 300 else ''}\n"
            )
    
    return "\n".join(sections)
```

**Formatted Output**:
```markdown
## 📋 Relevant Review Rules (from RAG):

1. **[R001]** (HIGH) Type Hints Required
   Use type hints. All function parameters and return values must have type annotations. This improves code readability and catches type errors early.

2. **[R003]** (MEDIUM) Docstrings Required
   Add docstrings. All functions must have docstrings explaining parameters, return values, and purpose.

## 📖 Relevant Project Guidelines (from RAG):

1. From `coding_guidelines.md` (project: cuongnln0812/pullpal-ai-agent):
   Our Python code must use type hints for all functions. The type hints should follow PEP 484 standards and use built-in generic types when possible...

2. From `coding_guidelines.md` (project: cuongnln0812/pullpal-ai-agent):
   DataFrame processing should always validate input schemas before processing. Use assert statements or raise ValueError for invalid inputs...
```

#### Step 16: Build Complete LLM Prompt (code_review_agent.py lines 344-357)
```python
# Build the complete prompt using the template
prompt = PROMPT_TEMPLATE.format(
    filename=filename,
    language=language,
    best_practices_text=best_practices_text + extended_rules_text + global_rules_text + ("\n\n" + rag_context if rag_context else ""),
    custom_guidelines_section=custom_guidelines_section,
    patch=patch
)
```

**Complete Prompt Structure**:
```markdown
You are an expert code reviewer. Review the following code changes from a GitHub Pull Request.

**File:** src/data_processor.py
**Language:** Python

**Best Practices for Python:**
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use context managers (with statements) for resource management
- Prefer list comprehensions over map/filter for readability
- Use logging instead of print statements
- Handle exceptions appropriately, avoid bare except

**Extended Best Practices:**
[Content from extended_rules.md - 3544 characters]

**Global Review Rules:**
- **[R001]** (HIGH) Type Hints Required
  - All functions must have type hints
  - Fix: Add type annotations to all parameters and return values
- **[R002]** (HIGH) Error Handling
  - Never use bare except
  - Fix: Use specific exception types

## 📋 Relevant Review Rules (from RAG):  ← RAG CONTEXT INJECTED HERE

1. **[R001]** (HIGH) Type Hints Required
   Use type hints. All function parameters and return values must have type annotations...

2. **[R003]** (MEDIUM) Docstrings Required
   Add docstrings. All functions must have docstrings...

## 📖 Relevant Project Guidelines (from RAG):  ← PROJECT-SPECIFIC CONTEXT

1. From `coding_guidelines.md` (project: cuongnln0812/pullpal-ai-agent):
   Our Python code must use type hints for all functions. The type hints should...

2. From `coding_guidelines.md` (project: cuongnln0812/pullpal-ai-agent):
   DataFrame processing should always validate input schemas before processing...

**Custom Project Guidelines:**
[Any inline guidelines provided by user]

**Code Changes (Git Diff):**
```diff
@@ -15,7 +15,8 @@ import pandas as pd
 
-def process_data(df):
+def process_data(df: pd.DataFrame) -> pd.DataFrame:
+    """Process dataframe and return cleaned version."""
     result = df.filter(lambda x: x['status'] == 'active')
     return result
```

**Instructions:**
Analyze the code changes and return a JSON array of issues found. Each issue should have:
- type: "bug", "security", "performance", or "style"
- message: Description of the issue
- suggestion: How to fix it
- line_start: Starting line number
- line_end: Ending line number (optional)
- code_snippet: The problematic code (optional)

Return ONLY the JSON array, no additional text.
```

**Key Point**: The LLM now has:
- ✅ General Python best practices
- ✅ Global coding rules
- ✅ **RAG-retrieved relevant rules** (semantic search)
- ✅ **RAG-retrieved project-specific guidelines** (filtered by project)
- ✅ The actual code to review

#### Step 17: Send to LLM (code_review_agent.py lines 359-361)
```python
response = client.invoke([HumanMessage(content=prompt)])
llm_output = response.content
```

**LLM Processing**:
1. Reads all context (best practices + RAG context + code)
2. Identifies issues based on the combined knowledge
3. Returns structured JSON response

**LLM Response**:
```json
[
  {
    "type": "style",
    "message": "Docstring added but could be more detailed",
    "suggestion": "Expand docstring to include parameter descriptions and return value details as per project guidelines",
    "line_start": 17,
    "line_end": 18,
    "code_snippet": "def process_data(df: pd.DataFrame) -> pd.DataFrame:\n    \"\"\"Process dataframe and return cleaned version.\"\"\""
  },
  {
    "type": "bug",
    "message": "Lambda function in filter may raise KeyError",
    "suggestion": "Add input validation before filtering as per project guideline: 'DataFrame processing should always validate input schemas'",
    "line_start": 19,
    "code_snippet": "result = df.filter(lambda x: x['status'] == 'active')"
  }
]
```

**Notice**: The suggestions reference the RAG-retrieved project guidelines! 🎯

#### Step 18: Parse & Enhance Response (code_review_agent.py lines 362-392)
```python
llm_issues = safe_parse_json(llm_output, filename)

# Extract code context
code_blocks = extract_code_context(patch)
sections = group_code_by_context(code_blocks)

# Enhance issues with line numbers and snippets
for issue in llm_issues:
    if "filename" not in issue:
        issue["filename"] = filename
    
    if "code_snippet" not in issue or not issue["code_snippet"]:
        if sections:
            first_section = sections[0]
            issue["line_start"] = first_section["start_line"]
            issue["line_end"] = first_section["end_line"]
            issue["code_snippet"] = "\n".join(
                f"{line['code']}" for line in first_section["lines"]
            )
```

#### Step 19: Update State (code_review_agent.py lines 395-400)
```python
if file_findings:
    findings.append({
        "filename": filename,
        "issues": file_findings
    })

state.findings = findings
return state
```

---

### Phase 4: Display Results

#### Step 20: Render in Streamlit UI (ui.py lines 95-150)
```python
st.subheader("📝 Code Review Findings")
if result['findings']:
    for f in result['findings']:
        with st.expander(f"📄 {f['filename']} ({len(f['issues'])} issue(s))"):
            for idx, issue in enumerate(f["issues"], 1):
                issue_type = issue['type'].upper()
                type_color = {
                    'BUG': '🐛',
                    'SECURITY': '🔒',
                    'PERFORMANCE': '⚡',
                    'STYLE': '💅'
                }.get(issue_type, '📌')
                
                st.markdown(f"### {type_color} Issue #{idx}: {issue_type}")
                
                if 'line_start' in issue:
                    st.caption(f"📍 Line {issue['line_start']}")
                
                if 'code_snippet' in issue:
                    st.code(issue['code_snippet'], language="python")
                
                st.markdown(f"**Issue:** {issue['message']}")
                st.info(f"💡 **Suggestion:** {issue['suggestion']}")
```

**Final UI Output**:
```
📝 Code Review Findings

▼ 📄 src/data_processor.py (2 issues)

  ### 💅 Issue #1: STYLE
  📍 Line 17
  
  Code:
  def process_data(df: pd.DataFrame) -> pd.DataFrame:
      """Process dataframe and return cleaned version."""
  
  Issue: Docstring added but could be more detailed
  
  💡 Suggestion: Expand docstring to include parameter descriptions 
  and return value details as per project guidelines
  
  ---
  
  ### 🐛 Issue #2: BUG
  📍 Line 19
  
  Code:
  result = df.filter(lambda x: x['status'] == 'active')
  
  Issue: Lambda function in filter may raise KeyError
  
  💡 Suggestion: Add input validation before filtering as per 
  project guideline: 'DataFrame processing should always validate input schemas'
```

---

## 🔑 Key Components Summary

### 1. **Storage Layer** (vector_store.py)
- **Purpose**: Store and retrieve coding guidelines and rules
- **Technology**: ChromaDB (vector database) + Sentence Transformers (embeddings)
- **Collections**:
  - `review_rules`: Global best practices
  - `project_guidelines`: User-uploaded project-specific guidelines
- **Key Methods**:
  - `store_project_guidelines()`: Store guideline files with embeddings
  - `search_relevant_rules()`: Find relevant global rules
  - `search_project_guidelines()`: Find relevant project guidelines (filtered by project)

### 2. **Retrieval Layer** (rag_retriever.py)
- **Purpose**: Retrieve relevant context for code review
- **Key Methods**:
  - `get_relevant_context()`: Search both rules and guidelines
  - `format_context_for_prompt()`: Format results for LLM
- **Filtering**: Ensures each project only sees its own guidelines

### 3. **Review Layer** (code_review_agent.py)
- **Purpose**: Perform code review using LLM + RAG context
- **Process**:
  1. Detect file language
  2. Retrieve RAG context
  3. Build comprehensive prompt
  4. Send to LLM
  5. Parse and enhance results
- **RAG Integration**: Lines 306-342

### 4. **UI Layer** (ui.py)
- **Purpose**: User interface for file upload and result display
- **Storage Trigger**: Lines 55-66 (when user clicks review button)
- **Result Display**: Lines 95-150 (shows issues found)

---

## 📊 Data Flow Summary

```
USER FILE → DECODE → CHUNK → EMBED → STORE IN CHROMADB
                                            ↓
                                    [Vector Database]
                                            ↓
REVIEW CODE → BUILD QUERY → VECTOR SEARCH → RETRIEVE CONTEXT
                                            ↓
                                  [RAG Context Retrieved]
                                            ↓
FORMAT CONTEXT → BUILD PROMPT → SEND TO LLM → PARSE RESPONSE
                                            ↓
                                    [Code Review Issues]
                                            ↓
                                    DISPLAY IN UI
```

---

## 🎯 RAG Benefits

1. **Semantic Search**: Finds relevant guidelines based on meaning, not keywords
   - Query: "How to handle database errors?"
   - Matches: "Database exceptions should be caught", "Use try-except for DB operations"

2. **Project Isolation**: Each project has its own guidelines
   - No cross-contamination between projects
   - Filtering by `project_name` ensures correct context

3. **Contextual Reviews**: LLM suggestions are informed by project-specific rules
   - Generic review: "Add error handling"
   - RAG-enhanced review: "Add error handling as per project guideline section 3.2"

4. **Scalable Knowledge**: Can store unlimited guidelines without prompt size limits
   - Only retrieves most relevant chunks (top 3)
   - No need to send entire guideline file to LLM

5. **Persistent Memory**: Guidelines stored once, used for all future reviews
   - Upload once, benefit forever
   - No need to re-upload for each PR

---

## 🛠 Technical Specifications

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Dimensions**: 384
- **Chunk Size**: ~500 characters
- **Search Results**: Top 5 rules + Top 3 guidelines
- **Similarity Metric**: Cosine similarity (via ChromaDB)
- **Database**: ChromaDB with persistent storage at `./chroma_db`
- **Supported File Types**: .md, .txt, .json
- **Encoding**: UTF-8 with error handling
