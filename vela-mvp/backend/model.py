from __future__ import annotations

import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

_provider = OpenAIProvider(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY", ""),
)

claude = OpenAIModel("meta-llama/llama-4-scout-17b-16e-instruct", provider=_provider)
