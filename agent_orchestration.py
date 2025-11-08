from langgraph.graph import StateGraph, END

from agents.doc_summarizer_agent import doc_summarizer_agent
from agents.pr_fetcher_agent import pr_fetcher_agent
from agents.code_review_agent import code_review_agent
from agents.test_coverage_agent import test_coverage_agent
from agents.state import PRSummaryAgentState

# --------------------------
# Initialize workflow graph
# --------------------------
graph = StateGraph(PRSummaryAgentState)  # Top-level state includes findings + coverage

# Add nodes
graph.add_node("pr_fetcher", pr_fetcher_agent)
graph.add_node("code_review", code_review_agent)
graph.add_node("test_coverage", test_coverage_agent)
graph.add_node("doc_summarizer", doc_summarizer_agent)

# Define workflow edges
graph.set_entry_point("pr_fetcher")
graph.add_edge("pr_fetcher", "code_review")
graph.add_edge("code_review", "test_coverage")
graph.add_edge("test_coverage", "doc_summarizer")
graph.add_edge("doc_summarizer", END)

# Compile workflow
workflow = graph.compile()


# --------------------------
# Run workflow
# --------------------------
if __name__ == "__main__":
    # Initialize state with PR URL
    mermaid_code = workflow.get_graph().draw_mermaid()
    print(mermaid_code)
    