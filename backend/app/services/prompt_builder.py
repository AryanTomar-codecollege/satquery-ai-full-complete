from __future__ import annotations


def has_spatial_intent(query: str) -> bool:
    q = (query or "").lower()
    terms = (
        "where", "locate", "location", "highlight", "mark", "show me", "find",
        "detect", "bounding", "bbox", "building", "buildings", "road", "roads",
        "water", "ship", "ships", "field", "fields", "vegetation patch", "region",
        "area of", "object", "objects", "cluster", "dense vegetation",
    )
    return any(term in q for term in terms)


def maybe_add_location_request(query: str, base_prompt: str, *, force: bool = False) -> str:
    if not force and not has_spatial_intent(query):
        return base_prompt
    return base_prompt + """

Also locate the main relevant regions when supported by the image.
Return machine-readable location evidence at the end using exactly this format:
BOXES:
- label: <feature>; bbox: [x1, y1, x2, y2]; space: normalized_1000
Use one BOXES line per region. Use normalized_1000 coordinates from 0 to 1000.
If the target cannot be located reliably, say uncertain and return no BOXES lines.
"""


def build_vqa_prompt(query: str) -> str:
    base = f"""You are a remote sensing analyst.
Analyze the satellite image carefully.
Answer the user question using only visible evidence.
Mention land cover, water, vegetation, built-up areas, roads, or agriculture when relevant.
Do not claim a feature that is not visibly supported by the image.
If the image is not coastal, do not say coast.
Be specific and concise in 4-8 sentences.
If uncertain, explicitly say so.

User question: {query.strip()}"""
    return maybe_add_location_request(query, base, force=True)


def build_caption_prompt(query: str = "") -> str:
    extra = f"\nUser request: {query.strip()}" if query.strip() else ""
    base = f"""Provide a detailed remote-sensing caption of this satellite image.
Describe dominant land cover, spatial pattern, possible land use, and notable features.
Do not invent place names, coordinates, dates, or objects that are not visible.
Use cautious language for interpretation rather than treating inference as fact.
Be specific but concise (4-8 sentences).{extra}"""
    return maybe_add_location_request(query, base)


def build_grounding_prompt(query: str) -> str:
    return f"""You are a remote sensing analyst.
Locate the requested feature(s) in the satellite image using only visible evidence.
Give the direct answer to the user question first.
Describe relative location such as upper-left, upper-right, center, lower-left, lower-right, or linear across the scene.
Prefer normalized_1000 coordinates so the boxes work across image sizes.
If multiple targets are visible, return multiple box lines.
If a target cannot be located reliably, say uncertain and return no box for that target.
Do not invent objects that are not visible.

Required machine-readable ending:
BOXES:
- label: <feature>; bbox: [x1, y1, x2, y2]; space: normalized_1000

User request: {query.strip()}"""


def build_change_prompt(query: str) -> str:
    base = f"""You are a remote sensing analyst comparing Image-1 and Image-2 as a bi-temporal observation.
Describe only changes supported by both images.
Identify what changed, what remained similar, and likely change type when supported:
built-up expansion, vegetation loss/gain, water change, agriculture change, or other visible land-cover change.
Do not invent changes caused by viewpoint, illumination, season, registration, or sensor differences; mention such uncertainty when relevant.
Be specific and structured:
1) Main changes
2) Stable areas
3) Confidence notes

User question: {query.strip()}"""
    return maybe_add_location_request(query, base, force=True)


def build_optical_sar_prompt(query: str) -> str:
    base = f"""You are a remote sensing analyst.
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
    return maybe_add_location_request(query, base, force=True)
