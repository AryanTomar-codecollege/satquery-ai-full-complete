from app.config import EARTHDIAL_MODEL
from app.services import geospatial
from app.tools import caption_tool, change_tool, grounding_tool, metadata_tool, optical_sar_tool, vqa_tool
from app.services import omniroute_client

def _text(x):
    return (x or "").strip().lower()

def select_task(query, task_hint, metas):
    forced = {
        "vqa": "vqa",
        "caption": "caption",
        "grounding": "grounding",
        "change": "change_detection",
        "optical_sar": "optical_sar",
        "metadata": "metadata",
    }
    hint = _text(task_hint or "auto")
    if hint in forced:
        return forced[hint]

    q = _text(query)
    if len(metas) >= 2 and any(x in q for x in (
        "change", "changed", "difference", "compare", "before and after", "temporal"
    )):
        return "change_detection"

    modalities = [geospatial.estimate_modality(m, m.get("filename", "")) for m in metas]
    if len(metas) >= 2 and (
        ("optical" in modalities and "sar" in modalities)
        or any(x in q for x in ("sar", "radar", "backscatter", "optical + sar", "optical and sar"))
    ):
        return "optical_sar"

    if any(x in q for x in ("where", "locate", "location", "bounding box", "bbox", "ground")):
        return "grounding"

    if any(x in q for x in ("metadata", "crs", "coordinate system", "resolution", "dimensions", "bands", "dtype")):
        return "metadata"

    if any(x in q for x in ("caption", "describe", "description", "land cover summary")):
        return "caption"

    return "vqa"

def _select_with_router(query, task_hint, metas):
    forced = {
        "vqa": "vqa",
        "caption": "caption",
        "grounding": "grounding",
        "change": "change_detection",
        "optical_sar": "optical_sar",
        "metadata": "metadata",
    }
    hint = _text(task_hint or "auto")
    if hint in forced:
        return forced[hint], "deterministic_forced", "task_hint explicitly selected the task."

    deterministic = select_task(query, "auto", metas)
    modalities = [geospatial.estimate_modality(m, m.get("filename", "")) for m in metas]

    if not omniroute_client.configured():
        return deterministic, "deterministic", "OmniRoute is disabled or not configured."

    try:
        routed = omniroute_client.choose_tool(query, len(metas), modalities, hint)
        tool = routed["tool"]
        if tool in {"metadata", "vqa", "caption", "grounding", "change_detection", "optical_sar"}:
            return tool, "omniroute", routed.get("reason", "") or "OmniRoute selected the specialist tool."
    except Exception as exc:
        return deterministic, "deterministic_fallback", f"OmniRoute failed: {str(exc)[:180]}"

    return deterministic, "deterministic_fallback", "OmniRoute returned an invalid tool."

def run(files_data, metas, query, task_hint="auto"):
    task, router, router_reason = _select_with_router(query, task_hint, metas)
    params = {
        "num_images": len(metas),
        "modalities": [
            geospatial.estimate_modality(m, m.get("filename", "")) for m in metas
        ],
    }

    if task == "metadata":
        result, tool = metadata_tool.run(files_data[0][1], files_data[0][0]), "metadata_tool"
    elif task == "caption":
        result, tool = caption_tool.run(files_data[0], query), "caption_tool"
    elif task == "grounding":
        result, tool = grounding_tool.run(files_data[0], files_data[0][1], query), "grounding_tool"
    elif task == "change_detection":
        result, tool = change_tool.run(files_data, query), "change_tool"
    elif task == "optical_sar":
        result, tool = optical_sar_tool.run(files_data, query), "optical_sar_tool"
    else:
        result, tool = vqa_tool.run(files_data[0], query), "vqa_tool"

    answer = result["answer"]
    if router == "omniroute":
        answer = omniroute_client.polish_answer(query, answer, task)

    trace = {
        "selected_task": task,
        "tools_used": [tool],
        "model_used": result.get("model_used", EARTHDIAL_MODEL),
        "parameters": {**params, **result.get("parameters", {})},
        "router": router,
        "router_reason": router_reason,
    }
    return {
        "answer": answer,
        "geojson": result["geojson"],
        "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.5)))),
        "execution_trace": trace,
        "model_used": trace["model_used"],
    }
