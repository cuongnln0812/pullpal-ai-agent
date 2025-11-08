"""LLM client adapter that routes to HOST_URL or langchain based on environment.

When HOST_URL is set, uses OpenAI SDK with custom base_url.
Otherwise, fall back to langchain_google_genai.ChatGoogleGenerativeAI.
"""
import os
from typing import List, Any


class LLMClient:
    """Unified LLM client supporting custom HOST_URL or langchain backends."""
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.0, host_url: str = None):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.host_url = host_url
        
        # If custom host, use OpenAI SDK with base_url
        if self.host_url:
            try:
                import openai
                self._openai_client = openai.OpenAI(
                    base_url=host_url,
                    api_key=api_key
                )
                self._langchain_client = None
            except ImportError as e:
                raise RuntimeError(
                    f"OpenAI package not installed. Run: pip install openai. Error: {e}"
                )
        else:
            # Fall back to langchain client
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._langchain_client = ChatGoogleGenerativeAI(
                    api_key=api_key,
                    model=model,
                    temperature=temperature
                )
                self._openai_client = None
            except Exception as e:
                raise RuntimeError(
                    f"Cannot initialize LLM: HOST_URL not set and langchain_google_genai unavailable. "
                    f"Set HOST_URL in .env or install langchain-google-genai. Error: {e}"
                )
    
    def invoke(self, messages: List[Any]) -> Any:
        """Invoke LLM with messages and return response object with .content attribute."""
        
        # Extract message content (handle both HumanMessage objects and strings)
        message_contents = []
        for msg in messages:
            if hasattr(msg, 'content'):
                message_contents.append(msg.content)
            else:
                message_contents.append(str(msg))
        
        # Route to OpenAI client or langchain
        if self._openai_client:
            return self._invoke_openai(message_contents)
        else:
            return self._langchain_client.invoke(messages)
    
    def _invoke_openai(self, message_contents: List[str]) -> Any:
        """Use OpenAI SDK to call custom endpoint."""
        # Convert to OpenAI message format
        openai_messages = [{"role": "user", "content": content} for content in message_contents]
        
        try:
            response = self._openai_client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature
            )
            
            # Extract content from OpenAI response
            content = response.choices[0].message.content
            
            # Return object mimicking langchain response
            class Response:
                pass
            
            resp = Response()
            resp.content = content
            return resp
            
        except Exception as e:
            raise RuntimeError(f"OpenAI client request failed: {e}")


def get_llm_client(convert_system_message_to_human: bool = False) -> LLMClient:
    """Factory function to create LLM client from environment variables.
    
    Args:
        convert_system_message_to_human: Ignored for custom hosts, used for langchain.
    
    Returns:
        LLMClient configured from environment.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GOOGLE_MODEL_NAME")
    temperature = float(os.getenv("GOOGLE_TEMPERATURE", "0.0"))
    host_url = os.getenv("HOST_URL")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set in environment or .env file")
    
    return LLMClient(
        api_key=api_key,
        model=model,
        temperature=temperature,
        host_url=host_url
    )
