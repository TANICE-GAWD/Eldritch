from __future__ import annotations

import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

_proxy_url = os.environ.get("AI_VERCEL_PROXY_URL", "")
_base_url = _proxy_url.replace("/chat/completions", "").rstrip("/")

_provider = OpenAIProvider(
    base_url=_base_url,
    api_key=os.environ.get("AI_VERCEL_PROXY_KEY", ""),
)

claude = OpenAIModel("anthropic/claude-sonnet-4-6", provider=_provider)
