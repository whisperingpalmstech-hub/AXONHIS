"""
Grok LLM client using the OpenAI-compatible API.

Model: llama-3.3-70b-versatile
Provider: Groq via https://api.groq.com/openai/v1
"""
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ANYTHING_LLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "7X1R879-1DS4X5M-NM0GS7H-A91JQZF")
ANYTHING_LLM_BASE_URL = os.getenv("ANYTHINGLLM_BASE_URL", "https://anythingllm.whispering-palms.org/api/v1/openai")
ANYTHING_LLM_MODEL = os.getenv("ANYTHINGLLM_MODEL", "my-workspace")


async def grok_chat(
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1024,
    response_format: str | None = None,
) -> dict[str, Any]:
    """
    Call AnythingLLM API (OpenAI-compatible) and return the parsed response dict.
    We kept the function name grok_chat so we don't have to rename it across the app.
    
    Returns:
        {"content": str, "usage": dict}
    """
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": ANYTHING_LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{ANYTHING_LLM_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {"content": content, "usage": usage}
    except httpx.HTTPStatusError as e:
        logger.error(f"AnythingLLM API HTTP error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"AnythingLLM API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException:
        logger.error("AnythingLLM API timeout")
        raise Exception("AnythingLLM API timeout - request took too long") from None
    except Exception as e:
        logger.error(f"AnythingLLM API error: {str(e)}")
        raise Exception(f"AnythingLLM API error: {str(e)}") from e


async def grok_json(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Call Grok and parse the response as JSON. Falls back to empty dict on parse error."""
    try:
        result = await grok_chat(messages, temperature=temperature, max_tokens=max_tokens, response_format="json")
        try:
            return json.loads(result["content"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Grok JSON parse error: %s | content=%s", e, result.get("content", ""))
            return {}
    except Exception as e:
        logger.error(f"Grok JSON API call failed: {str(e)}")
        return {}
