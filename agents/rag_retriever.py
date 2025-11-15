"""
RAG Retriever for enhanced code review context.

Retrieves relevant information from vector store to augment LLM prompts.
"""

from typing import List, Dict, Any, Optional
from agents.vector_store import get_vector_store


class RAGRetriever:
    """Retrieves relevant context from vector store for code review."""
    
    def __init__(self):
        """Initialize RAG retriever with vector store."""
        self.vector_store = get_vector_store()
    
    def get_relevant_context(self, code_snippet: str, language: str, 
                            project_name: Optional[str] = None,
                            max_rules: int = 5,
                            max_guidelines: int = 3) -> Dict[str, Any]:
        """Get all relevant context for reviewing a code snippet.
        
        Args:
            code_snippet: Code to review
            language: Programming language
            project_name: Project name for filtering guidelines
            max_rules: Maximum number of rules to retrieve
            max_guidelines: Maximum number of guideline chunks to retrieve
            
        Returns:
            Dictionary with relevant rules and guidelines
        """
        # Build search query combining code and language
        query = f"{language} code review: {code_snippet}"
        
        # Search for relevant rules
        relevant_rules = self.vector_store.search_relevant_rules(
            query=query,
            n_results=max_rules
        )
        
        # Search for relevant project guidelines
        relevant_guidelines = self.vector_store.search_project_guidelines(
            query=query,
            project_name=project_name,
            n_results=max_guidelines
        )
        
        return {
            "rules": relevant_rules,
            "guidelines": relevant_guidelines,
            "query": query
        }
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format retrieved context into a string for LLM prompt.
        
        Args:
            context: Context dictionary from get_relevant_context()
            
        Returns:
            Formatted string to include in prompt
        """
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
        
        if not sections:
            return ""
        
        return "\n".join(sections)
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with collection counts
        """
        return self.vector_store.get_collection_stats()


# Singleton instance
_rag_retriever = None

def get_rag_retriever() -> RAGRetriever:
    """Get or create singleton RAG retriever instance."""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    return _rag_retriever
