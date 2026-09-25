from __future__ import annotations
import re

UNCERTAIN_WORDS = (
    "uncertain", "not sure", "may be", "might be", "could be", "possibly",
    "appears to", "appears", "likely", "difficult to tell",
    "cannot reliably", "not clearly",
)

def estimate_confidence(task: str, answer: str, *, spatial_features: int = 0) -> float:
    base = {
        "vqa": 0.74,
        "caption": 0.76,
        "grounding": 0.66,
        "change": 0.72,
        "optical_sar": 0.74,
        "metadata": 0.90,
    }.get(task, 0.70)

    text = re.sub(r"\s+", " ", (answer or "").strip())
    sentence_count = len([s for s in re.split(r"[.!?]+", text) if s.strip()])

    if len(text) < 80:
        base -= 0.08
    elif sentence_count < 3 and task not in {"metadata", "grounding"}:
        base -= 0.04

    hits = sum(1 for word in UNCERTAIN_WORDS if word in text.lower())
    base -= min(0.10, hits * 0.02)

    if task == "grounding":
        base += 0.08 if spatial_features > 0 else -0.06

    return round(max(0.55, min(0.90, base)), 2)
