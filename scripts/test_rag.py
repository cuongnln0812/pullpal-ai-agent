"""
Test script to verify RAG system is working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all RAG dependencies are installed."""
    print("\n" + "="*60)
    print("🧪 Testing RAG Imports")
    print("="*60)
    
    try:
        import chromadb
        print("✓ chromadb imported")
    except ImportError:
        print("❌ chromadb not found. Install: pip install chromadb>=0.4.22")
        return False
    
    try:
        import sentence_transformers
        print("✓ sentence_transformers imported")
    except ImportError:
        print("❌ sentence_transformers not found. Install: pip install sentence-transformers>=2.2.2")
        return False
    
    try:
        from agents.vector_store import get_vector_store
        print("✓ vector_store module imported")
    except ImportError as e:
        print(f"❌ vector_store import failed: {e}")
        return False
    
    try:
        from agents.rag_retriever import get_rag_retriever
        print("✓ rag_retriever module imported")
    except ImportError as e:
        print(f"❌ rag_retriever import failed: {e}")
        return False
    
    return True


def test_vector_store():
    """Test vector store initialization and basic operations."""
    print("\n" + "="*60)
    print("🧪 Testing Vector Store")
    print("="*60)
    
    try:
        from agents.vector_store import get_vector_store
        
        # Initialize vector store
        vector_store = get_vector_store()
        print("✓ Vector store initialized")
        
        # Test embedding generation
        test_texts = ["This is a test", "Another test sentence"]
        embeddings = vector_store.generate_embeddings(test_texts)
        print(f"✓ Generated embeddings: {len(embeddings)} vectors of dimension {len(embeddings[0])}")
        
        # Test storing a simple rule
        test_rule = {
            "id": "TEST1",
            "title": "Test Rule",
            "description": "This is a test rule",
            "fix": "This is how to fix it",
            "severity": "info",
            "scope": "*"
        }
        vector_store.store_review_rules([test_rule], source="test")
        print("✓ Stored test rule")
        
        # Test searching
        results = vector_store.search_relevant_rules("test rule", n_results=1)
        if results:
            print(f"✓ Search successful: Found {len(results)} result(s)")
        else:
            print("⚠️ Search returned no results (this might be expected if DB is empty)")
        
        # Get stats
        stats = vector_store.get_collection_stats()
        print(f"✓ Collection stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_retriever():
    """Test RAG retriever functionality."""
    print("\n" + "="*60)
    print("🧪 Testing RAG Retriever")
    print("="*60)
    
    try:
        from agents.rag_retriever import get_rag_retriever
        
        # Initialize retriever
        retriever = get_rag_retriever()
        print("✓ RAG retriever initialized")
        
        # Test getting context
        test_code = """
        def get_user(user_id):
            return User.query.filter_by(id=user_id).get()
        """
        
        context = retriever.get_relevant_context(
            code_snippet=test_code,
            language="Python",
            project_name="test",
            max_rules=3,
            max_guidelines=2
        )
        
        print(f"✓ Retrieved context:")
        print(f"  - Rules: {len(context.get('rules', []))}")
        print(f"  - Guidelines: {len(context.get('guidelines', []))}")
        
        # Test formatting
        formatted = retriever.format_context_for_prompt(context)
        if formatted:
            print(f"✓ Formatted context: {len(formatted)} characters")
        else:
            print("ℹ️ No context to format (DB might be empty)")
        
        # Get stats
        stats = retriever.get_stats()
        print(f"✓ Retriever stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG retriever test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_review_integration():
    """Test that code_review_agent can use RAG."""
    print("\n" + "="*60)
    print("🧪 Testing Code Review Integration")
    print("="*60)
    
    try:
        from agents import code_review_agent
        
        if hasattr(code_review_agent, 'RAG_ENABLED'):
            if code_review_agent.RAG_ENABLED:
                print("✓ RAG is enabled in code_review_agent")
            else:
                print("⚠️ RAG is disabled in code_review_agent")
                return False
        else:
            print("⚠️ RAG_ENABLED flag not found in code_review_agent")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Code review integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 RAG System Test Suite")
    print("="*60)
    
    results = {
        "Imports": test_imports(),
        "Vector Store": test_vector_store(),
        "RAG Retriever": test_rag_retriever(),
        "Code Review Integration": test_code_review_integration()
    }
    
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All tests passed! RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python scripts/seed_knowledge_base.py")
        print("2. Start UI: streamlit run ui.py")
        print("3. Upload project guidelines and review a PR!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("- Install dependencies: pip install chromadb sentence-transformers")
        print("- Check that files exist: agents/vector_store.py, agents/rag_retriever.py")
    
    print()
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
