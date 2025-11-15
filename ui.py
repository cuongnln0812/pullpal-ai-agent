import streamlit as st
from github_fetcher import parse_github_pr_url
from agent_orchestration import workflow
from agents.state import PRSummaryAgentState

st.set_page_config(page_title="🛠 PR Review Agent", layout="wide")
st.title("🛠 PR Review Agent")

# --------------------------
# Step 1: Input PR URL
# --------------------------
pr_url = st.text_input(
    "Enter GitHub PR URL",
    placeholder=""
)

# --------------------------
# Step 1b: GitHub Personal Access Token (optional)
# --------------------------
token = st.text_input(
    "GitHub Personal Access Token (for private repos)",
    placeholder="ghp_xxxxxxx",
    type="password"
)

# --------------------------
# Step 1c: Optional project guideline file
# --------------------------
guideline_file = st.file_uploader(
    "Upload project coding guideline / rules (optional, .md, .txt, .json)",
    type=["md", "txt", "json"]
)

# --------------------------
# Step 1d: Start Review Button
# --------------------------
if st.button("🚀 Start PR Review") and pr_url:
    try:
        # Parse PR URL & initialize state
        pr_info = parse_github_pr_url(pr_url)
        custom_guidelines = guideline_file.read().decode("utf-8") if guideline_file else None
        state = PRSummaryAgentState(pr_url=pr_url, custom_guidelines=custom_guidelines)
        state.github_token = token if token else None
        # Store full project identifier (owner/repo format)
        state.project_name = f"{pr_info['owner']}/{pr_info['repo']}"

        # Read guideline file content (if provided)
        if guideline_file is not None:
            guideline_bytes = guideline_file.getvalue()
            try:
                guideline_content = guideline_bytes.decode("utf-8", errors="ignore")
                state.guideline_text = guideline_content
                
                # 🆕 Store in RAG vector database
                try:
                    from agents.vector_store import get_vector_store
                    with st.spinner(f"📝 Storing {guideline_file.name} in RAG database..."):
                        vector_store = get_vector_store()
                        # Store with full project path (owner/repo) for proper filtering
                        vector_store.store_project_guidelines(
                            content=guideline_content,
                            filename=guideline_file.name,
                            project_name=f"{pr_info['owner']}/{pr_info['repo']}"
                        )
                    st.success(f"✅ Guidelines stored in RAG: {guideline_file.name}")
                except ImportError:
                    st.warning("⚠️ RAG not available (install: pip install chromadb sentence-transformers)")
                except Exception as e:
                    st.warning(f"⚠️ Could not store in RAG: {e}")
            except Exception:
                # Fallback: best-effort decoding
                state.guideline_text = guideline_bytes.decode(errors="ignore")

        with st.spinner("Fetching PR and analyzing... This may take a few seconds"):
            result = workflow.invoke(state)

        # --------------------------
        # PR Overview
        # --------------------------
        st.subheader("📄 PR Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"**👤 Owner:** {result['owner']}")
        col1.markdown(f"**📦 Repo:** {result['repo']}")
        col2.markdown(f"**#️⃣ PR Number:** {result['pr_number']}")
        col2.markdown(f"**📝 Files Changed:** {len(result['files'])}")

        # --------------------------
        # Code Review Findings
        # --------------------------
        st.subheader("📝 Code Review Findings")
        if result['findings']:
            for f in result['findings']:
                with st.expander(f"📄 {f['filename']} ({len(f['issues'])} issue{'s' if len(f['issues']) != 1 else ''})"):
                    for idx, issue in enumerate(f["issues"], 1):
                        # Issue header with badge
                        issue_type = issue['type'].upper()
                        type_color = {
                            'BUG': '🐛',
                            'SECURITY': '🔒',
                            'PERFORMANCE': '⚡',
                            'STYLE': '💅'
                        }.get(issue_type, '📌')
                        source_label = {
                            'global': '🌐 Global Rule',
                            'user': '👤 User Rule',
                            'rag': '📚 RAG Rule'
                        }.get(issue.get('source', 'global'), '🌐 Global Rule')
                        st.markdown(f"### {type_color} Issue #{idx}: {issue_type} [{source_label}]")
                        # Display line numbers if available
                        if 'line_start' in issue and issue.get('line_start'):
                            if issue.get('line_end') and issue['line_end'] != issue['line_start']:
                                st.caption(f"📍 Lines {issue['line_start']}-{issue['line_end']}")
                            else:
                                st.caption(f"📍 Line {issue['line_start']}")
                        # Display code snippet if available
                        if 'code_snippet' in issue and issue.get('code_snippet'):
                            st.markdown("**Code:**")
                            import os
                            _, ext = os.path.splitext(f['filename'])
                            lang_map = {
                                '.py': 'python', '.java': 'java', '.js': 'javascript',
                                '.ts': 'typescript', '.go': 'go', '.rb': 'ruby',
                                '.php': 'php', '.cs': 'csharp', '.cpp': 'cpp',
                                '.c': 'c', '.rs': 'rust', '.kt': 'kotlin'
                            }
                            language = lang_map.get(ext.lower(), 'text')
                            st.code(issue['code_snippet'], language=language)
                        st.markdown(f"**Issue:** {issue['message']}")
                        st.info(f"💡 **Suggestion:** {issue['suggestion']}")
                        # Show detailed rule info if available
                        if issue.get('rule_id') or issue.get('rule_title'):
                            st.markdown("---")
                            st.markdown(f"**Rule ID:** {issue.get('rule_id', 'N/A')}")
                            st.markdown(f"**Rule Title:** {issue.get('rule_title', 'N/A')}")
                            st.markdown(f"**Rule Description:** {issue.get('rule_description', 'N/A')}")
                            st.markdown(f"**Rule Fix:** {issue.get('rule_fix', 'N/A')}")
                        # Add a clear button for each issue (for demonstration, does not persist)
                        if st.button(f"Clear Issue #{idx} [{source_label}]", key=f"clear_{f['filename']}_{idx}"):
                            st.success(f"Issue #{idx} cleared!")
                        if idx < len(f['issues']):
                            st.divider()
        else:
            st.info("✅ No code review issues detected.")

        # --------------------------
        # Test Coverage Findings
        # --------------------------
        st.subheader("🧪 Test Coverage Findings")
        if result['coverage_findings']:
            for f in result['coverage_findings']:
                with st.expander(f"{f['filename']} ({len(f.get('generated_tests',[]))} test stubs)"):
                    st.markdown(f"**Issue:** {f['issue']}")
                    st.markdown(f"**Message:** {f['message']}")
                    st.markdown(f"*Suggestion:* {f['suggestion']}")
                    for t in f.get("generated_tests", []):
                        st.markdown(f"**Generated Test File:** {t['filename']}")
                        st.code(t["code"], language="python")
        else:
            st.info("✅ No missing tests detected.")

        # --------------------------
        # PR Summary
        # --------------------------
        st.subheader("🖊 PR Summary")
        pr_summary = getattr(result, "pr_summary", None) or result.get("pr_summary", "")
        if pr_summary:
            st.success(pr_summary)
        else:
            st.warning("PR summary not available.")

    except Exception as e:
        st.error(f"❌ Error processing PR: {e}")