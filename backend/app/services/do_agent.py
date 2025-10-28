import httpx
from typing import Any, Dict, List

async def call_do_agent(
    base_url: str,
    access_key: str,
    messages: List[Dict[str, str]],
    include_retrieval_info: bool = True,
    include_functions_info: bool = False,
    include_guardrails_info: bool = False,
    stream: bool = False,
) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {access_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": messages,
        "stream": stream,
        "include_retrieval_info": include_retrieval_info,
        "include_functions_info": include_functions_info,
        "include_guardrails_info": include_guardrails_info,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()
