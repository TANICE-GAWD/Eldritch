from __future__ import annotations

import os
import uuid
from typing import Any

from supabase import AsyncClient, acreate_client


async def _client() -> AsyncClient:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return await acreate_client(url, key)


async def create_job(input_data: dict[str, Any]) -> str:
    client = await _client()
    result = await client.table("jobs").insert({
        "id": str(uuid.uuid4()),
        "status": "pending",
        "input": input_data,
    }).execute()
    return result.data[0]["id"]


async def update_job(job_id: str, status: str, output: dict[str, Any] | None = None) -> None:
    client = await _client()
    payload: dict[str, Any] = {"status": status}
    if output is not None:
        payload["output"] = output
    await client.table("jobs").update(payload).eq("id", job_id).execute()


async def get_job(job_id: str) -> dict[str, Any] | None:
    client = await _client()
    result = await client.table("jobs").select("*").eq("id", job_id).execute()
    return result.data[0] if result.data else None
