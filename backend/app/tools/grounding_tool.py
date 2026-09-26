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
    r"(?:bbox\s*[:=]?\s*)?[\[\(]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[\]\)]", re.I
)


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


def run(file_tuple, file_bytes: bytes, query: str):
    result = infer(file_tuple, build_grounding_prompt(query), "[grounding]")
    answer = str(result.get("answer", "")).strip()
    features = []
    boxes = parse_boxes(answer)
    for label, bbox, space in boxes:
        try:
            features.append(pixel_bbox_to_geojson_feature(file_bytes, bbox, space, label))
        except Exception:
            try:
                pixel_bbox = normalize_bbox_to_pixel(file_bytes, bbox, space)
                features.append({
                    "type": "Feature",
                    "properties": {"label": label, "bbox_pixel": pixel_bbox, "bbox_space": space},
                    "geometry": None,
                })
            except Exception:
                continue
    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": features},
        "confidence": estimate_confidence("grounding", answer, spatial_features=len(features)),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[grounding]"),
            "boxes_parsed": len(features),
            "bbox_space": "normalized_1000",
        },
    }
