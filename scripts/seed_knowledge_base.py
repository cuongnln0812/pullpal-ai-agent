"""
Seed the vector database with initial knowledge.

Loads:
- Global review rules from prompts/global_review_rules.json
- Extended rules from extended_rules.md (optional)
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vector_store import get_vector_store


def load_global_rules(rules_path: Path) -> list:
    """Load global review rules from JSON file."""
    try:
        with rules_path.open('r', encoding='utf-8') as f:
            rules = json.load(f)
        print(f"✓ Loaded {len(rules)} global rules from {rules_path.name}")
        return rules
    except Exception as e:
        print(f"⚠️ Error loading global rules: {e}")
        return []


def load_extended_rules(rules_path: Path) -> str:
    """Load extended rules from markdown file."""
    try:
        if not rules_path.exists():
            print(f"ℹ️ Extended rules file not found at {rules_path}")
            return ""
        
        with rules_path.open('r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Loaded extended rules from {rules_path.name} ({len(content)} chars)")
        return content
    except Exception as e:
        print(f"⚠️ Error loading extended rules: {e}")
        return ""


def main():
    """Seed the vector database with initial knowledge."""
    print("\n" + "="*60)
    print("🌱 Seeding Knowledge Base")
    print("="*60 + "\n")
    
    # Initialize vector store
    vector_store = get_vector_store()
    
    # Get paths
    base_dir = Path(__file__).parent.parent
    global_rules_path = base_dir / "prompts" / "global_review_rules.json"
    extended_rules_path = base_dir / "extended_rules.md"
    
    # Load and store global rules
    print("\n📋 Loading Global Review Rules...")
    global_rules = load_global_rules(global_rules_path)
    if global_rules:
        vector_store.store_review_rules(global_rules, source="global")
    
    # Load and store extended rules as guideline
    print("\n📖 Loading Extended Rules...")
    extended_rules = load_extended_rules(extended_rules_path)
    if extended_rules:
        vector_store.store_project_guidelines(
            content=extended_rules,
            filename="extended_rules.md",
            project_name="system"
        )
    
    # Show statistics
    print("\n" + "="*60)
    print("📊 Knowledge Base Statistics")
    print("="*60)
    stats = vector_store.get_collection_stats()
    for collection, count in stats.items():
        print(f"  {collection}: {count} documents")
    
    print("\n✅ Knowledge base seeded successfully!")
    print(f"📁 Database location: {vector_store.persist_directory}\n")


if __name__ == "__main__":
    main()
