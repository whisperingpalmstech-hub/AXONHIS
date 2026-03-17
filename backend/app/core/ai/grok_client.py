"""
Grok LLM client using the OpenAI-compatible API.

Model: llama-3.3-70b-versatile
Provider: Grok (xAI) via https://api.x.ai/v1
"""
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GROK_API_KEY = "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"
GROK_BASE_URL = "https://api.groq.com/openai/v1"
GROK_MODEL = "llama-3.3-70b-versatile"


async def grok_chat(
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1024,
    response_format: str | None = None,
) -> dict[str, Any]:
    """
    Call Grok API (OpenAI-compatible) and return the parsed response dict.

    Returns:
        {"content": str, "usage": dict}
    """
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": GROK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{GROK_BASE_URL}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return {"content": content, "usage": usage}


async def grok_json(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Call Grok and parse the response as JSON. Falls back to empty dict on parse error."""
    result = await grok_chat(messages, temperature=temperature, max_tokens=max_tokens, response_format="json")
    try:
        return json.loads(result["content"])
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Grok JSON parse error: %s | content=%s", e, result.get("content", ""))
        return {}
