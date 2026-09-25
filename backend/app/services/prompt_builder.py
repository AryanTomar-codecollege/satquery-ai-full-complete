from __future__ import annotations

def build_vqa_prompt(query: str) -> str:
    return f"""You are a remote sensing analyst.
Analyze the satellite image carefully.
Answer the user question using only visible evidence.
Mention land cover, water, vegetation, built-up areas, roads, or agriculture when relevant.
Do not claim a feature that is not visibly supported by the image.
If the image is not coastal, do not say coast.
Be specific and concise in 4-8 sentences.
If uncertain, explicitly say so.

User question: {query.strip()}"""


def build_caption_prompt(query: str = "") -> str:
    extra = f"\nUser request: {query.strip()}" if query.strip() else ""
    return f"""Provide a detailed remote-sensing caption of this satellite image.
Describe dominant land cover, spatial pattern, possible land use, and notable features.
Do not invent place names, coordinates, dates, or objects that are not visible.
Use cautious language for interpretation rather than treating inference as fact.
Be specific but concise (4-8 sentences).{extra}"""


def build_grounding_prompt(query: str) -> str:
    return f"""You are a remote sensing analyst.
Locate the requested feature(s) in the satellite image using only visible evidence.
Do not invent objects that are not visible.
If possible, return approximate bounding regions for each requested target.
Describe relative image position such as upper-left, center, lower-right, or linear across the scene.
When returning boxes, use [x1, y1, x2, y2] and state the coordinate space explicitly as pixel, normalized_1, or normalized_1000.
If the target cannot be located reliably, say uncertain instead of guessing.

User request: {query.strip()}"""


def build_change_prompt(query: str) -> str:
    return f"""You are a remote sensing analyst comparing Image-1 and Image-2 as a bi-temporal observation.
Describe only changes supported by both images.
Identify what changed, what remained similar, and likely change type when supported:
built-up expansion, vegetation loss/gain, water change, agriculture change, or other visible land-cover change.
Do not invent changes caused by viewpoint, illumination, season, registration, or sensor differences; mention such uncertainty when relevant.
Be specific and structured:
1) Main changes
2) Stable areas
3) Confidence notes

User question: {query.strip()}"""


def build_optical_sar_prompt(query: str) -> str:
    return f"""You are a remote sensing analyst.
Perform joint Optical + SAR remote-sensing analysis.
Treat Image-1 and Image-2 as a paired optical/SAR observation.
Use optical cues such as color, texture, vegetation pattern, water, built-up areas, roads, and agriculture.
Use SAR cues such as backscatter brightness/darkness, surface roughness, structure, and water response.
Explain what each modality contributes, then give a cautious joint interpretation.
Use only evidence visible in the supplied images.
Do not invent coastlines, water bodies, buildings, ships, roads, or land-cover classes not supported by the scene.
Be specific and concise. Structure the answer exactly as:
1) Optical observations
2) SAR observations
3) Joint interpretation
4) Uncertainties

User question: {query.strip()}"""
