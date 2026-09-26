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
    r"(?:bbox\s*[:=]?\s*)?\[\(?\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[, ]\s*"
    r"(-?\d+(?:\.\d+)?)\s*[\]\)]",
    re.I,
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

# Bounding boxes are initially kept in normalized_1000 space.  Nearby boxes
# are clustered before conversion to image pixels so the same logic works for
# GeoTIFFs of different sizes.
MERGE_GAP = 65.0


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


def _clip_normalized_bbox(bbox):
    x1, y1, x2, y2 = [float(v) for v in bbox]
    x1, x2 = sorted((max(0.0, min(1000.0, x1)), max(0.0, min(1000.0, x2))))
    y1, y2 = sorted((max(0.0, min(1000.0, y1)), max(0.0, min(1000.0, y2))))
    return [x1, y1, x2, y2]


def _bbox_gap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    gap_x = max(ax1 - bx2, bx1 - ax2, 0.0)
    gap_y = max(ay1 - by2, by1 - ay2, 0.0)
    return gap_x, gap_y


def _should_merge(a, b, threshold=MERGE_GAP):
    """Merge overlapping/nearby boxes, including boxes touching on one axis."""
    gap_x, gap_y = _bbox_gap(a, b)
    return gap_x <= threshold and gap_y <= threshold


def _merge_two(a, b):
    return [
        min(a[0], b[0]),
        min(a[1], b[1]),
        max(a[2], b[2]),
        max(a[3], b[3]),
    ]


def merge_nearby_boxes(items, threshold=MERGE_GAP):
    """
    Cluster nearby/overlapping boxes into larger regions.

    Each item is (label, bbox, space).  The output uses normalized_1000 boxes.
    Merging is transitive: A close to B and B close to C produces one region.
    Boxes that are far apart remain separate regions.
    """
    normalized = []

    for label, bbox, space in items:
        try:
            if space == "normalized_1000":
                nb = _clip_normalized_bbox(bbox)
            elif space == "normalized_1":
                nb = _clip_normalized_bbox([float(v) * 1000.0 for v in bbox])
            else:
                # Pixel-space boxes cannot be safely merged with normalized
                # boxes without image dimensions. Keep them as-is; conversion
                # happens later and the original evidence is preserved.
                normalized.append((label, bbox, space))
                continue
            if nb[2] > nb[0] and nb[3] > nb[1]:
                normalized.append((label, nb, "normalized_1000"))
        except (TypeError, ValueError):
            continue

    groups = [
        {"labels": [label], "bbox": list(bbox), "space": space}
        for label, bbox, space in normalized
    ]

    # Repeatedly merge until no more groups can be joined. This makes the
    # clustering transitive instead of depending on EarthDial's output order.
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            if changed:
                break
            for j in range(i + 1, len(groups)):
                a = groups[i]
                b = groups[j]
                if a["space"] != "normalized_1000" or b["space"] != "normalized_1000":
                    continue
                if _should_merge(a["bbox"], b["bbox"], threshold):
                    a["bbox"] = _merge_two(a["bbox"], b["bbox"])
                    a["labels"].extend(b["labels"])
                    groups.pop(j)
                    changed = True
                    break

    merged = []
    for group in groups:
        label = group["labels"][0] if group["labels"] else "detected feature"
        merged.append((label, group["bbox"], group["space"]))
    return merged


def _relative_region(answer: str):
    text = re.sub(r"\s+", " ", (answer or "").lower())
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


def _convert_feature(file_bytes, label, bbox, space):
    try:
        return pixel_bbox_to_geojson_feature(file_bytes, bbox, space, label)
    except Exception:
        try:
            pixel_bbox = normalize_bbox_to_pixel(file_bytes, bbox, space)
            return {
                "type": "Feature",
                "properties": {
                    "label": label,
                    "bbox_pixel": pixel_bbox,
                    "bbox_space": space,
                },
                "geometry": None,
            }
        except Exception:
            return None


def run(file_tuple, file_bytes: bytes, query: str):
    result = infer(file_tuple, build_grounding_prompt(query), "[grounding]")
    answer = str(result.get("answer", "")).strip()

    raw_boxes = parse_boxes(answer)
    boxes = merge_nearby_boxes(raw_boxes)
    features = []
    evidence_source = "model_box"
    merged_count = max(0, len(raw_boxes) - len(boxes))

    for label, bbox, space in boxes:
        feature = _convert_feature(file_bytes, label, bbox, space)
        if feature:
            features.append(feature)

    # Fallback only when EarthDial supplied a relative location but omitted
    # machine-readable boxes. It remains explicitly approximate.
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
            "raw_boxes_parsed": len(raw_boxes),
            "merged_regions": merged_count,
            "bbox_space": "normalized_1000",
            "merge_gap_normalized": MERGE_GAP,
            "evidence_source": evidence_source,
            "approximate_boxes": sum(
                1 for f in features
                if f.get("properties", {}).get("approximate") is True
            ),
        },
    }
