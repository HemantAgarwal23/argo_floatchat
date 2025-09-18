"""
multi_llm_client.py
Unified client that routes between Groq and Hugging Face Inference API
"""
from typing import Dict, Any, List, Optional, Tuple
import time
import json
import re
import structlog
import requests

from app.config import settings
from app.core.llm_client import GroqLLMClient


logger = structlog.get_logger()


def _estimate_tokens(text: str) -> int:
    """Very rough token estimator (~4 chars per token)."""
    if not text:
        return 0
    # Approximate: tokens ≈ words * 1.3
    words = len(text.split())
    return max(1, int(words * 1.3))


class HuggingFaceClient:
    """Thin wrapper for Hugging Face Inference API text/code generation."""

    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.base_url = settings.HUGGINGFACE_API_URL.rstrip('/') + '/'
        self.text_model = settings.HF_TEXT_MODEL
        self.code_model = settings.HF_CODE_MODEL
        self.fallback_model = settings.HF_FALLBACK_MODEL
        self.max_tokens = settings.HF_MAX_TOKENS
        self.temperature = settings.HF_TEMPERATURE

        if not self.api_key:
            logger.warning("Hugging Face API key is not set. Calls will fail.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _invoke(self, model: str, inputs: List[Dict[str, str]],
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop: Optional[List[str]] = None) -> str:
        url = self.base_url + model
        payload = {
            "inputs": self._convert_chat_to_prompt(inputs),
            "parameters": {
                "temperature": temperature if temperature is not None else self.temperature,
                "max_new_tokens": max_tokens if max_tokens is not None else self.max_tokens,
                "return_full_text": False,
            }
        }
        if stop:
            payload["parameters"]["stop"] = stop

        try:
            response = requests.post(url, headers=self._headers(), data=json.dumps(payload), timeout=60)
            response.raise_for_status()
            data = response.json()
            # Inference API returns list of dicts with 'generated_text'
            if isinstance(data, list) and data and 'generated_text' in data[0]:
                return data[0]['generated_text'].strip()
            # Some deployments return a dict
            if isinstance(data, dict) and 'generated_text' in data:
                return data['generated_text'].strip()
            # Fallback parsing
            return json.dumps(data)
        except Exception as e:
            logger.error("Hugging Face API call failed", model=model, error=str(e))
            raise

    def _convert_chat_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        parts: List[str] = []
        for m in messages:
            role = m.get('role', 'user')
            content = m.get('content', '')
            if role == 'system':
                parts.append(f"[SYSTEM]\n{content}\n")
            elif role == 'assistant':
                parts.append(f"[ASSISTANT]\n{content}\n")
            else:
                parts.append(f"[USER]\n{content}\n")
        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)

    def generate(self, messages: List[Dict[str, str]], use_code_model: bool = False,
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        model = self.code_model if use_code_model else self.text_model
        try:
            return self._invoke(model, messages, temperature=temperature, max_tokens=max_tokens)
        except Exception:
            logger.warning("Primary HF model failed, trying fallback", model=model)
            return self._invoke(self.fallback_model, messages, temperature=temperature, max_tokens=max_tokens)


class MultiLLMClient:
    """Routes requests between Groq and Hugging Face with automatic fallback."""

    def __init__(self):
        self.groq = GroqLLMClient()
        self.hf = HuggingFaceClient()
        self.groq_hard_limit = settings.GROQ_HARD_TOKEN_LIMIT

    def _should_use_hf(self, user_query: str, messages: List[Dict[str, str]]) -> bool:
        text = (user_query or "") + "\n" + "\n".join(m.get('content', '') for m in messages)
        text_lower = text.lower()

        # Keywords indicating visualization/coordinates
        if any(kw in text_lower for kw in ["map", "coordinates", "visualization", "plot", "geojson", "plotly"]):
            return True

        # Estimate tokens; if above Groq hard limit, use HF
        estimated = _estimate_tokens(text)
        if estimated > self.groq_hard_limit:
            return True

        return False

    def _log_provider_use(self, provider: str, user_query: str, tokens: int, success: bool, fallback: bool = False):
        logger.info(
            "LLM provider used",
            provider=provider,
            estimated_tokens=tokens,
            success=success,
            fallback=fallback,
            query_preview=user_query[:160]
        )

    def generate_response(self, messages: List[Dict[str, str]],
                          user_query: Optional[str] = None,
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None,
                          use_code_model: bool = False) -> str:
        user_query = user_query or next((m.get('content') for m in messages if m.get('role') == 'user'), '')
        estimated = _estimate_tokens("\n".join(m.get('content', '') for m in messages))

        # Preferred provider selection
        use_hf = self._should_use_hf(user_query, messages)
        providers: List[Tuple[str, str]] = [('hf', 'primary'), ('groq', 'fallback')] if use_hf else [('groq', 'primary'), ('hf', 'fallback')]

        last_error: Optional[Exception] = None
        for provider, role in providers:
            try:
                if provider == 'groq':
                    result = self.groq.generate_response(messages, temperature=temperature, max_tokens=max_tokens)
                    self._log_provider_use('groq', user_query, estimated, True, fallback=(role == 'fallback'))
                    return result
                else:
                    result = self.hf.generate(messages, use_code_model=use_code_model, temperature=temperature, max_tokens=max_tokens)
                    self._log_provider_use('huggingface', user_query, estimated, True, fallback=(role == 'fallback'))
                    return result
            except Exception as e:
                last_error = e
                self._log_provider_use(provider, user_query, estimated, False, fallback=(role == 'fallback'))
                continue

        # If both providers fail
        logger.error("Both providers failed", error=str(last_error) if last_error else "unknown")
        raise RuntimeError(f"All providers failed: {str(last_error)}")

    # Back-compat helpers mirroring existing GroqLLMClient public methods
    def classify_query_type(self, user_query: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "Classify oceanographic queries into sql_retrieval, vector_retrieval, or hybrid_retrieval and extract entities as JSON."},
            {"role": "user", "content": f"Classify this oceanographic query: {user_query}"}
        ]
        try:
            response = self.generate_response(messages, user_query=user_query, temperature=0.1)
            return json.loads(response)
        except Exception:
            # Fallback to Groq implementation if parsing fails
            try:
                return self.groq.classify_query_type(user_query)
            except Exception:
                return {"query_type": "vector_retrieval", "confidence": 0.3, "extracted_entities": {}, "reasoning": "classification failed"}

    def generate_final_response(self, user_query: str, retrieved_data: Dict[str, Any], query_type: str) -> str:
        # Reuse Groq prompts to keep behavior, but route via selection
        system_prompt = self.groq.get_system_prompt(query_type, len(retrieved_data.get('sql_results', [])), bool(retrieved_data.get('sql_results')))
        system_prompt += f"\nThe user asked: \"{user_query}\"\nQuery type: {query_type}\nReport exactly what the database contains, nothing more."
        data_summary = self.groq._summarize_data_for_llm(retrieved_data)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Retrieved database results: {data_summary}\nReport exactly what this data contains for the user's query."}
        ]

        # If the query mentions map/coordinates/visualization, prefer HF for higher token output
        prefer_code = any(kw in user_query.lower() for kw in ["plotly", "matplotlib", "visualization", "map", "coordinates", "geojson"])
        temperature = 0.1 if query_type == 'sql_retrieval' else 0.2
        try:
            return self.generate_response(messages, user_query=user_query, temperature=temperature, use_code_model=prefer_code)
        except Exception:
            # Final fallback to Groq implementation
            return self.groq.generate_final_response(user_query, retrieved_data, query_type)


# Global multi-provider client instance
multi_llm_client = MultiLLMClient()


