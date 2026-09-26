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

# Approximate fallback only when EarthDial gives a relative location.
RELATIVE_REGION_BBOXES = {
    "upper-left": [0, 0, 500, 500],
    "upper-right": [500, 0, 1000, 500],
    "lower-left": [0, 500, 500, 1000],
    "lower-right": [500, 500, 1000, 1000],
    "center": [250, 250, 750, 750],
    "left": [0, 150, 500, 850],
    "right": [500, 150, 1000, 850],
    "upper": [100, 0, 900, 500],
    "lower": [100, 500, 900, 1000],
}

# Merge overlapping/nearby normalized boxes so one continuous feature
# does not appear as many separate rectangles.
MERGE_GAP = 65.0


def parse_boxes(answer):
    parsed = []
    consumed = set()

    for match in BOX_LINE_RE.finditer(answer or ""):
        nums = [float(x.strip()) for x in match.group("bbox").replace(",", " ").split()]
        if len(nums) == 4:
            parsed.append(
                (
                    match.group("label").strip(),
                    nums,
                    match.group("space").lower(),
                )
            )
            consumed.add(match.span())

    for match in BOX_RE.finditer(answer or ""):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        parsed.append(
            ("detected feature", [float(x) for x in match.groups()], "pixel")
        )

    return parsed


def _clip_normalized_bbox(bbox):
    x1, y1, x2, y2 = [float(v) for v in bbox]
    x1, x2 = sorted(
        (
            max(0.0, min(1000.0, x1)),
            max(0.0, min(1000.0, x2)),
        )
    )
    y1, y2 = sorted(
        (
            max(0.0, min(1000.0, y1)),
            max(0.0, min(1000.0, y2)),
        )
    )
    return [x1, y1, x2, y2]


def _bbox_gap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    gap_x = max(ax1 - bx2, bx1 - ax2, 0.0)
    gap_y = max(ay1 - by2, by1 - ay2, 0.0)
    return gap_x, gap_y


def _should_merge(a, b, threshold=MERGE_GAP):
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
    Merge overlapping/nearby normalized boxes transitively.
    Distant regions remain separate.
    Pixel-space boxes are preserved without unsafe cross-space merging.
    """
    groups = []
    passthrough = []

    for label, bbox, space in items:
        try:
            if space == "normalized_1000":
                nb = _clip_normalized_bbox(bbox)
            elif space == "normalized_1":
                nb = _clip_normalized_bbox([float(v) * 1000.0 for v in bbox])
            else:
                passthrough.append((label, bbox, space))
                continue

            if nb[2] > nb[0] and nb[3] > nb[1]:
                groups.append({"labels": [label], "bbox": nb})
        except (TypeError, ValueError):
            continue

    changed = True
    while changed:
        changed = False

        for i in range(len(groups)):
            merged = False

            for j in range(i + 1, len(groups)):
                if _should_merge(groups[i]["bbox"], groups[j]["bbox"], threshold):
                    groups[i]["bbox"] = _merge_two(
                        groups[i]["bbox"], groups[j]["bbox"]
                    )
                    groups[i]["labels"].extend(groups[j]["labels"])
                    groups.pop(j)
                    changed = True
                    merged = True
                    break

            if merged:
                break

    merged = [
        (
            group["labels"][0] if group["labels"] else "detected feature",
            group["bbox"],
            "normalized_1000",
        )
        for group in groups
    ]

    return merged + passthrough


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
    merged_boxes = merge_nearby_boxes(raw_boxes)
    features = []
    evidence_source = "model_box"

    for label, bbox, space in merged_boxes:
        feature = _convert_feature(file_bytes, label, bbox, space)
        if feature:
            features.append(feature)

    merged_count = max(0, len(raw_boxes) - len(merged_boxes))

    # Fallback only when EarthDial gives relative location but no machine boxes.
    if not features:
        relative = _relative_region(answer)

        if relative:
            key, bbox = relative

            try:
                pixel_bbox = normalize_bbox_to_pixel(
                    file_bytes,
                    bbox,
                    "normalized_1000",
                )

                features.append(
                    {
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
                    }
                )

                evidence_source = "model_relative_location"
            except Exception:
                pass

    return {
        "answer": answer,
        "geojson": {
            "type": "FeatureCollection",
            "features": features,
        },
        "confidence": estimate_confidence(
            "grounding",
            answer,
            spatial_features=len(features),
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
                1
                for feature in features
                if feature.get("properties", {}).get("approximate") is True
            ),
        },
    }
