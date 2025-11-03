import streamlit as st
from github_fetcher import parse_github_pr_url
from pr_graph import workflow
from agents.state import TestCoverageAgentState

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
# Step 1c: Start Review Button
# --------------------------
if st.button("🚀 Start PR Review") and pr_url:
    try:
        # Parse PR URL & initialize state
        pr_info = parse_github_pr_url(pr_url)
        state = TestCoverageAgentState(pr_url=pr_url)
        state.github_token = token if token else None

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
                with st.expander(f"{f['filename']} ({len(f['issues'])} issues)"):
                    for issue in f["issues"]:
                        st.markdown(f"**[{issue['type'].upper()}]** {issue['message']}")
                        st.markdown(f"*Suggestion:* {issue['suggestion']}")
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