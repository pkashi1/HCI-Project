"""
LLM client wrapper for Ollama API.
Handles chat completions with local models.
"""
import requests
import json
from typing import List, Dict, Optional


class OllamaClient:
    """Client for interacting with local Ollama models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "gemma3:1b"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API endpoint
            default_model: Default model to use (phi4, llama3.2:3b-instruct, etc.)
        """
        self.base_url = base_url
        self.default_model = self._get_available_model(default_model)
        self.chat_endpoint = f"{base_url}/api/chat"
    
    def _get_available_model(self, preferred_model: str) -> str:
        """
        Get available model with fallback logic.
        
        Args:
            preferred_model: Preferred model name
            
        Returns:
            Available model name
        """
        available_models = self.list_models()
        
        if not available_models:
            return preferred_model
        
        # Check exact match or prefix match (e.g., phi4 matches phi4:latest)
        for model in available_models:
            if model == preferred_model or model.startswith(f"{preferred_model}:"):
                return model
        
        # Fallback order
        fallback_order = ["phi4", "gemma3:1b", "llama3.2:3b-instruct", "llama3.2:1b"]
        
        for fallback in fallback_order:
            for model in available_models:
                if model == fallback or model.startswith(f"{fallback}:"):
                    return model
        
        return available_models[0]
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False
    ) -> str:
        """
        Send chat completion request to Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (uses default if None)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated text response
            
        Raises:
            requests.HTTPError: If API request fails
            ValueError: If response format is invalid
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=300  # 5 min timeout for large models like phi4
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract message content
            if "message" not in data:
                raise ValueError(f"Unexpected response format: {data}")
            
            return data["message"]["content"]
            
        except requests.exceptions.Timeout:
            # Try fallback model if timeout occurs
            if model != "gemma3:1b":
                print(f"⚠ {model} timed out, trying fallback model...")
                fallback_payload = payload.copy()
                fallback_payload["model"] = "gemma3:1b"
                
                try:
                    response = requests.post(
                        self.chat_endpoint,
                        json=fallback_payload,
                        timeout=60
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]
                except:
                    pass
            
            raise Exception(f"Request to {model} timed out after 120 seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Could not connect to Ollama. Is it running? "
                "Start it with: ollama serve"
            )
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
    
    def check_health(self) -> bool:
        """
        Check if Ollama service is running.
        
        Returns:
            True if service is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []


# Global client instance (lazy initialization)
_client = None


def get_client(model: str = "gemma3:1b") -> OllamaClient:
    """
    Get or create global Ollama client instance.
    
    Args:
        model: Default model to use
        
    Returns:
        OllamaClient instance
    """
    global _client
    if _client is None:
        _client = OllamaClient(default_model=model)
    return _client


def chat(messages: List[Dict[str, str]], model: str = "gemma3:1b", temperature: float = 0.7) -> str:
    """
    Convenience function for chat completion with automatic fallback.
    
    Args:
        messages: List of message dicts
        model: Model to use
        temperature: Sampling temperature
        
    Returns:
        Generated response text
    """
    client = get_client()
    
    # Try preferred model first
    try:
        return client.chat(messages, model=model, temperature=temperature)
    except Exception as e:
        if "timed out" in str(e) or "not found" in str(e):
            # Try fallback models
            fallback_models = ["gemma3:1b", "llama3.2:3b-instruct"]
            for fallback in fallback_models:
                try:
                    available = client.list_models()
                    if any(fallback in m for m in available):
                        print(f"⚠ Falling back to {fallback}")
                        return client.chat(messages, model=fallback, temperature=temperature)
                except:
                    continue
        raise e


def extract_json_from_response(text: str) -> str:
    """
    Extract JSON from response that might contain markdown or extra text.
    
    Args:
        text: Raw LLM response
        
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks if present
    text = text.strip()
    
    if text.startswith("```"):
        # Find content between code fences
        lines = text.split("\n")
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = len(lines)
        
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end_idx = i
                break
        
        text = "\n".join(lines[start_idx:end_idx])
    
    # Try to extract JSON object/array
    import re
    
    # Find first { or [ and last } or ]
    json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    return text


# CLI test interface
if __name__ == "__main__":
    print("Testing Ollama connection...")
    
    client = get_client()
    
    # Check health
    if not client.check_health():
        print("ERROR: Ollama is not running!")
        print("Start it with: ollama serve")
        exit(1)
    
    print("✓ Ollama is running")
    
    # List models
    models = client.list_models()
    print(f"\nAvailable models: {', '.join(models)}")
    
    if not models:
        print("\nNo models found! Pull one with:")
        print("  ollama pull phi4")
        exit(1)
    
    # Test chat
    print("\nTesting chat completion...")
    test_messages = [
        {"role": "user", "content": "Say 'Hello from Ollama!' and nothing else."}
    ]
    
    try:
        response = chat(test_messages)
        print(f"Response: {response}")
        print("\n✓ Chat completion working!")
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)