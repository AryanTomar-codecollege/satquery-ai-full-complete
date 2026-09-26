from __future__ import annotations
import re
from typing import Iterable
from app.services.geospatial import pixel_bbox_to_geojson_feature, normalize_bbox_to_pixel

BOX_LINE_RE = re.compile(r"label\s*:\s*(?P<label>[^;\n]+)\s*;\s*bbox\s*:\s*\[(?P<bbox>[^\]]+)\]\s*;\s*space\s*:\s*(?P<space>normalized_1000|normalized_1|pixel)", re.I)
BOX_RE = re.compile(r"(?:bbox\s*[:=]?\s*)?[\[\(]\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*[\]\)]", re.I)


def parse_boxes(answer: str):
    parsed, consumed = [], []
    for m in BOX_LINE_RE.finditer(answer or ""):
        nums = [float(x.strip()) for x in m.group("bbox").replace(",", " ").split()]
        if len(nums) == 4:
            parsed.append((m.group("label").strip(), nums, m.group("space").lower()))
            consumed.append(m.span())
    for m in BOX_RE.finditer(answer or ""):
        if any(a <= m.start() < b for a, b in consumed):
            continue
        parsed.append(("detected feature", [float(x) for x in m.groups()], "pixel"))
    return parsed


def geojson_from_answer(data: bytes, answer: str):
    features = []
    for label, bbox, space in parse_boxes(answer):
        try:
            features.append(pixel_bbox_to_geojson_feature(data, bbox, space, label))
        except Exception:
            try:
                pixel_bbox = normalize_bbox_to_pixel(data, bbox, space)
                features.append({
                    "type": "Feature",
                    "properties": {"label": label, "bbox_pixel": pixel_bbox, "bbox_space": space},
                    "geometry": None,
                })
            except Exception:
                pass
    return {"type": "FeatureCollection", "features": features}


def geojson_from_multiple(files_data: Iterable, answer: str):
    # For multi-image answers, attach returned boxes to the first image by default.
    # This keeps the existing API shape while allowing the primary uploaded image to be highlighted.
    first = next(iter(files_data), None)
    return geojson_from_answer(first[1], answer) if first else {"type": "FeatureCollection", "features": []}
