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


def maybe_add_location_request(
    query: str,
    base_prompt: str,
    *,
    force: bool = False,
) -> str:
    if not force and not has_spatial_intent(query):
        return base_prompt

    return base_prompt + """

Also locate the requested feature across the ENTIRE image.

IMPORTANT GROUNDING INSTRUCTIONS:
- Scan the whole image from left to right and top to bottom before deciding.
- Do not stop after finding the first visible part.
- A requested feature may extend across a large portion of the image.
- For a large continuous feature, return MULTIPLE reasonably tight boxes
  covering its different visible parts.
- If those boxes belong to one connected/nearby feature, the backend will
  merge them into one region.
- If the feature occurs in clearly separated distant regions, return a
  separate BOXES line for each region.
- Do not use "upper-right" or another quadrant as a substitute for actual
  coordinates when machine-readable coordinates can be estimated.

Use exactly:
BOXES:
- label: <feature>; bbox: [x1, y1, x2, y2]; space: normalized_1000

Rules:
- Coordinates must be normalized_1000 from 0 to 1000.
- Return one BOXES line per supported region/part.
- Keep boxes reasonably tight around the visible feature.
- Cover the visible extent of the requested feature, not just the first part.
- Do not invent coordinates or objects.
- If exact coordinates truly cannot be determined, state the best supported
  relative location and omit BOXES.
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
    return f"""You are a remote sensing analyst performing a spatial grounding task.

Locate ALL visible regions of the requested feature(s) across the ENTIRE
satellite image.

Carefully scan the complete image before producing coordinates.

IMPORTANT:
- Do not stop after the first visible occurrence.
- If the requested feature is a large continuous area, return multiple
  tight/overlapping boxes covering its different visible parts.
- If those nearby boxes describe the same continuous feature, the backend will
  merge them into one final region.
- If there are clearly separated distant instances, return separate boxes.
- Do not reduce a large feature to only "upper-left", "upper-right", etc.
- Keep every box reasonably tight around the actual visible feature.

Your final section MUST contain:

BOXES:
- label: <feature>; bbox: [x1, y1, x2, y2]; space: normalized_1000

Rules:
- Coordinates must be normalized_1000 from 0 to 1000.
- Use one BOXES line per supported region/part.
- Scan the whole image before deciding.
- Cover the full visible extent of the requested feature.
- Do not use a whole-image or quadrant box unless the actual feature occupies it.
- Do not invent coordinates or objects.
- If machine-readable coordinates truly cannot be determined, state the best
  supported relative location and omit BOXES.

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
