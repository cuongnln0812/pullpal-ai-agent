"""Compatibility shim for HumanMessage to avoid langchain dependency issues.

When langchain is available, use the real HumanMessage.
Otherwise, provide a minimal fallback dataclass.
"""

try:
    from langchain_core.messages import HumanMessage
except ImportError:
    try:
        from langchain.schema import HumanMessage
    except ImportError:
        # Fallback: minimal implementation
        from dataclasses import dataclass
        
        @dataclass
        class HumanMessage:
            """Minimal HumanMessage fallback for when langchain is not available."""
            content: str

__all__ = ["HumanMessage"]
