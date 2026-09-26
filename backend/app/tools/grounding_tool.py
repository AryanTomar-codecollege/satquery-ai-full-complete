import re
from app.services.geospatial import pixel_bbox_to_geojson_feature, normalize_bbox_to_pixel
from app.services.kaggle_client import infer
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_grounding_prompt

BOX_LINE_RE = re.compile(
    r"label\s*:\s*(?P<label>[^;\n]+)\s*;\s*bbox\s*:\s*\[(?P<bbox>[^\]]+)\]\s*;\s*space\s*:\s*(?P<space>normalized_1000|normalized_1|pixel)",
    re.I,
)
BOX_RE = re.compile(
    r"(?:bbox\s*[:=]?\s*)?\[\(\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[\]\)]", re.I
)

# EarthDial sometimes answers a grounding question with a relative position
# ("upper left", "center", etc.) but omits the machine-readable BOXES block.
# This fallback preserves that model evidence as an explicitly approximate
# spatial region instead of pretending it is an exact detection.
RELATIVE_REGION_BBOXES = {
    "upper-left": [0, 0, 550, 550],
    "upper-right": [450, 0, 1000, 550],
    "lower-left": [0, 450, 550, 1000],
    "lower-right": [450, 450, 1000, 1000],
    "center": [250, 250, 750, 750],
    "left": [0, 100, 600, 900],
    "right": [400, 100, 1000, 900],
    "upper": [0, 0, 1000, 600],
    "lower": [0, 400, 1000, 1000],
}

def parse_boxes(answer):
    parsed = []
    consumed = set()
    for match in BOX_LINE_RE.finditer(answer or ""):
        nums = [float(x.strip()) for x in match.group("bbox").replace(",", " ").split()]
        if len(nums) == 4:
            parsed.append((match.group("label").strip(), nums, match.group("space").lower()))
            consumed.add(match.span())

    for match in BOX_RE.finditer(answer or ""):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        parsed.append(("detected feature", [float(x) for x in match.groups()], "pixel"))
    return parsed


def _relative_region(answer: str):
    text = re.sub(r"\s+", " ", (answer or "").lower())
    # Check diagonals before single-axis positions.
    patterns = (
        (r"\bupper[\s-]+left\b|\btop[\s-]+left\b", "upper-left"),
        (r"\bupper[\s-]+right\b|\btop[\s-]+right\b", "upper-right"),
        (r"\blower[\s-]+left\b|\bbottom[\s-]+left\b", "lower-left"),
        (r"\blower[\s-]+right\b|\bbottom[\s-]+right\b", "lower-right"),
        (r"\bcenter(?:ed)?\b|\bcentral\b|\bmiddle\b", "center"),
        (r"\bleft(?:\s+side)?\b", "left"),
        (r"\bright(?:\s+side)?\b", "right"),
        (r"\bupper(?:\s+part|\s+portion)?\b|\btop(?:\s+part|\s+portion)?\b", "upper"),
        (r"\blower(?:\s+part|\s+portion)?\b|\bbottom(?:\s+part|\s+portion)?\b", "lower"),
    )
    for pattern, key in patterns:
        if re.search(pattern, text):
            return key, RELATIVE_REGION_BBOXES[key]
    return None


def _target_label(query: str) -> str:
    text = re.sub(
        r"\b(where|is|are|the|a|an|please|highlight|locate|location|find|show|me|mark|detect|"
        r"identify|in|on|this|image|satellite|area|areas)\b",
        " ",
        query or "",
        flags=re.I,
    )
    text = re.sub(r"\s+", " ", text).strip(" ?.,")
    return text[:80] or "Requested feature"


def run(file_tuple, file_bytes: bytes, query: str):
    result = infer(file_tuple, build_grounding_prompt(query), "[grounding]")
    answer = str(result.get("answer", "")).strip()
    features = []
    boxes = parse_boxes(answer)
    evidence_source = "model_box"

    for label, bbox, space in boxes:
        try:
            features.append(pixel_bbox_to_geojson_feature(file_bytes, bbox, space, label))
        except Exception:
            try:
                pixel_bbox = normalize_bbox_to_pixel(file_bytes, bbox, space)
                features.append({
                    "type": "Feature",
                    "properties": {
                        "label": label,
                        "bbox_pixel": pixel_bbox,
                        "bbox_space": space,
                    },
                    "geometry": None,
                })
            except Exception:
                continue

    # Fallback only when EarthDial explicitly supplied a relative location
    # but omitted BOXES. The box is deliberately marked approximate.
    if not features:
        relative = _relative_region(answer)
        if relative:
            key, bbox = relative
            try:
                pixel_bbox = normalize_bbox_to_pixel(
                    file_bytes, bbox, "normalized_1000"
                )
                features.append({
                    "type": "Feature",
                    "properties": {
                        "label": _target_label(query),
                        "bbox_pixel": pixel_bbox,
                        "bbox_space": "pixel",
                        "evidence_source": "model_relative_location",
                        "approximate": True,
                        "relative_location": key,
                    },
                    "geometry": None,
                })
                evidence_source = "model_relative_location"
            except Exception:
                pass

    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": features},
        "confidence": estimate_confidence(
            "grounding", answer, spatial_features=len(features)
        ),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[grounding]"),
            "boxes_parsed": len(features),
            "bbox_space": "normalized_1000",
            "evidence_source": evidence_source,
            "approximate_boxes": sum(
                1 for f in features
                if f.get("properties", {}).get("approximate") is True
            ),
        },
    }
