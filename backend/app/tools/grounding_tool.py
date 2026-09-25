import re
from app.services.geospatial import pixel_bbox_to_geojson_feature
from app.services.kaggle_client import infer
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_grounding_prompt

BOX_RE = re.compile(
    r"(?:bbox\s*[:=]?\s*)?[\[\(]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[\]\)]", re.I
)

def _parse_boxes(answer):
    return [[float(x) for x in m.groups()] for m in BOX_RE.finditer(answer or "")]

def _space(answer):
    text = (answer or "").lower()
    if "normalized_1000" in text or "0-1000" in text:
        return "normalized_1000"
    if "normalized_1" in text or "0-1" in text:
        return "normalized_1"
    return "pixel"

def run(file_tuple, file_bytes: bytes, query: str):
    result = infer(file_tuple, build_grounding_prompt(query), "[grounding]")
    answer = str(result.get("answer", "")).strip()
    space = _space(answer)
    features = []
    for bbox in _parse_boxes(answer):
        try:
            features.append(pixel_bbox_to_geojson_feature(file_bytes, bbox, space))
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
            "bbox_space": space,
        },
    }
