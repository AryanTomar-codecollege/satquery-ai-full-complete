from __future__ import annotations
import json
from typing import Dict, List
import httpx
from app.config import OMNIROUTE_API_KEY, OMNIROUTE_BASE_URL, OMNIROUTE_MODEL, OMNIROUTE_TIMEOUT, omniroute_configured

ALLOWED_TOOLS = {"metadata", "vqa", "caption", "grounding", "change_detection", "optical_sar"}

def configured() -> bool:
    return omniroute_configured()

def _url() -> str:
    return OMNIROUTE_BASE_URL.rstrip("/") + "/chat/completions"

def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {OMNIROUTE_API_KEY}", "Content-Type": "application/json"}

def _extract_json(content: str) -> Dict:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("OmniRoute did not return a JSON object.")
    return json.loads(content[start:end + 1])

def choose_tool(query: str, num_images: int, modalities: List[str], task_hint: str = "auto") -> Dict:
    if not configured():
        raise RuntimeError("OmniRoute is not configured.")
    system = (
        "You are the query router for SatQuery AI. Choose exactly one specialist tool. "
        "Return only valid JSON with keys \"tool\" and \"reason\". Do not analyze image pixels. "
        "Available tools: metadata, vqa, caption, grounding, change_detection, optical_sar. "
        "Use grounding whenever the user wants to find, show, highlight, mark, locate, detect, "
        "or identify the position/region of an object such as buildings, roads, water, ships, fields, vegetation, or areas. "
        "Use change_detection for two images and temporal/before-after/change comparisons. "
        "Use optical_sar for optical+SAR paired requests. Use metadata for CRS/dimensions/bands/dtype/resolution questions. "
        "Use caption for describe/scene-description requests. Use vqa for other image questions."
    )
    user = f"query={query}\nnum_images={num_images}\nmodalities={modalities}\ntask_hint={task_hint}"
    response = httpx.post(_url(), headers=_headers(), json={
        "model": OMNIROUTE_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
    }, timeout=OMNIROUTE_TIMEOUT)
    response.raise_for_status()
    parsed = _extract_json(response.json()["choices"][0]["message"]["content"])
    tool = str(parsed.get("tool", "")).strip()
    if tool not in ALLOWED_TOOLS:
        raise ValueError(f"OmniRoute returned unsupported tool: {tool}")
    return {"tool": tool, "reason": str(parsed.get("reason", "")).strip()[:300]}

def polish_answer(query: str, answer: str, selected_task: str) -> str:
    return answer
