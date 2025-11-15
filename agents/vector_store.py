"""
Vector Store for RAG-enhanced Code Review.

Stores and retrieves:
- Global review rules
- User-provided project guidelines
- Past review findings (optional)
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    """Vector database for storing and retrieving code review knowledge."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize vector store with persistent storage.
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize OpenAI client for embeddings
        api_key = os.getenv("EMBEDDING_API_KEY")
        base_url = os.getenv("EMBEDDING_BASE_URL")
        
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY or OPENAI_API_KEY must be set in .env file")
        
        self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536  # text-embedding-3-small default dimensions
        
        # Create or get collections
        self.rules_collection = self.client.get_or_create_collection(
            name="review_rules",
            metadata={"description": "Global and project-specific review rules"}
        )
        
        self.guidelines_collection = self.client.get_or_create_collection(
            name="project_guidelines",
            metadata={"description": "User-provided project documentation and guidelines"}
        )
        
        print(f"✓ Vector store initialized at {persist_directory}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI text-embedding-3-small.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (1536 dimensions each)
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            raise
    
    def store_review_rules(self, rules: List[Dict[str, Any]], source: str = "global"):
        """Store review rules in vector database.
        
        Args:
            rules: List of rule dictionaries with keys: id, title, severity, description, fix
            source: Source of rules ("global" or "project")
        """
        if not rules:
            print("⚠️ No rules to store")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for rule in rules:
            rule_id = rule.get("id", "unknown")
            title = rule.get("title", "")
            description = rule.get("description", "")
            fix = rule.get("fix", "")
            severity = rule.get("severity", "info")
            scope = rule.get("scope", "*")
            
            # Combine rule info into searchable document
            doc_text = f"{title}. {description} Fix: {fix}"
            documents.append(doc_text)
            
            # Store metadata
            metadatas.append({
                "rule_id": rule_id,
                "title": title,
                "severity": severity,
                "scope": scope,
                "source": source,
                "type": "review_rule"
            })
            
            ids.append(f"{source}_{rule_id}")
        
        # Generate embeddings
        embeddings = self.generate_embeddings(documents)
        
        # Store in ChromaDB
        self.rules_collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Stored {len(rules)} {source} rules")
    
    def store_project_guidelines(self, content: str, filename: str, project_name: str = "default"):
        """Store user-provided project guidelines/documentation.
        
        Args:
            content: Text content of the guideline document
            filename: Name of the source file
            project_name: Name of the project (format: "owner/repo" or just "repo")
        """
        if not content.strip():
            print("⚠️ Empty content, skipping")
            return
        
        # Extract owner from project_name if in "owner/repo" format
        owner = None
        if "/" in project_name:
            parts = project_name.split("/", 1)
            owner = parts[0]
        
        # Split content into chunks (by paragraphs or sections)
        chunks = self._chunk_text(content)
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
                
            documents.append(chunk)
            # Store both full project path and owner separately for flexible filtering
            metadata = {
                "filename": filename,
                "project": project_name,
                "chunk_index": idx,
                "source": "user_guideline",
                "type": "project_guideline"
            }
            if owner:
                metadata["owner"] = owner  # Add GitHub username/owner for filtering
            metadatas.append(metadata)
            
            # Sanitize ID to replace "/" with "_"
            safe_project_name = project_name.replace("/", "_")
            ids.append(f"{safe_project_name}_{filename}_{idx}")
        
        if not documents:
            print("⚠️ No valid chunks to store")
            return
        
        # Generate embeddings
        embeddings = self.generate_embeddings(documents)
        
        # Store in ChromaDB
        self.guidelines_collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Stored {len(documents)} chunks from {filename}")
    
    def search_relevant_rules(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant review rules based on code/issue query.
        
        Args:
            query: Search query (code snippet, issue description, etc.)
            n_results: Number of results to return
            
        Returns:
            List of relevant rules with metadata
        """
        if not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Search in rules collection
        results = self.rules_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        relevant_rules = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                relevant_rules.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return relevant_rules
    
    def search_project_guidelines(self, query: str, project_name: Optional[str] = None, 
                                  owner: Optional[str] = None, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant project guidelines.
        
        Args:
            query: Search query
            project_name: Filter by full project name "owner/repo" (optional)
            owner: Filter by GitHub owner/username (optional)
            n_results: Number of results to return
            
        Returns:
            List of relevant guideline chunks with metadata
        """
        if not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Build filter based on provided parameters
        where = None
        if project_name:
            where = {"project": project_name}
        elif owner:
            where = {"owner": owner}
        
        # Search in guidelines collection
        results = self.guidelines_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Format results
        relevant_guidelines = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                relevant_guidelines.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return relevant_guidelines
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for embedding.
        
        Args:
            text: Text to chunk
            chunk_size: Approximate size of each chunk in characters
            
        Returns:
            List of text chunks
        """
        # Split by double newlines (paragraphs) first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk size, save current and start new
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored data.
        
        Returns:
            Dictionary with collection counts
        """
        return {
            "review_rules": self.rules_collection.count(),
            "project_guidelines": self.guidelines_collection.count()
        }


# Singleton instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
