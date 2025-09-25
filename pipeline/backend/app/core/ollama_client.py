"""
Ollama LLM Client for local model inference
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama client for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL
            model: Model name to use
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 120  # 2 minutes timeout for local inference
        
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Ollama API"""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise Exception(f"Ollama API request failed: {str(e)}")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = self._make_request("generate", data)
            return response.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            raise Exception(f"Ollama text generation failed: {str(e)}")
    
    def generate_code(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """
        Generate code using Ollama
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated code
        """
        try:
            # Add code-specific instructions to the prompt
            code_prompt = f"""You are a helpful assistant that generates SQL queries for oceanographic data analysis. 
            Generate clean, efficient SQL code based on the user's request.

            {prompt}

            Return only the SQL query without any explanations or markdown formatting."""
            
            data = {
                "model": self.model,
                "prompt": code_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = self._make_request("generate", data)
            return response.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Ollama code generation failed: {e}")
            raise Exception(f"Ollama code generation failed: {str(e)}")
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        try:
            # Convert messages to a single prompt for Ollama
            prompt = self._messages_to_prompt(messages)
            
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = self._make_request("generate", data)
            return response.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise Exception(f"Ollama chat completion failed: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt for Ollama"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == self.model:
                        return model
            return {"name": self.model, "status": "unknown"}
        except:
            return {"name": self.model, "status": "unavailable"}
