import io
import re

import numpy as np
import rasterio
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

MERGE_GAP = 65.0


def parse_boxes(answer):
    parsed, consumed = [], set()

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
    x1, x2 = sorted((max(0, min(1000, x1)), max(0, min(1000, x2))))
    y1, y2 = sorted((max(0, min(1000, y1)), max(0, min(1000, y2))))
    return [x1, y1, x2, y2]


def _gap(a, b):
    return (
        max(a[0] - b[2], b[0] - a[2], 0),
        max(a[1] - b[3], b[1] - a[3], 0),
    )


def merge_nearby_boxes(items, threshold=MERGE_GAP):
    groups = []
    passthrough = []

    for label, bbox, space in items:
        if space == "normalized_1000":
            bbox = _clip_normalized_bbox(bbox)
        elif space == "normalized_1":
            bbox = _clip_normalized_bbox([float(v) * 1000 for v in bbox])
        else:
            passthrough.append((label, bbox, space))
            continue

        if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            groups.append({"label": label, "bbox": bbox})

    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                gx, gy = _gap(groups[i]["bbox"], groups[j]["bbox"])
                if gx <= threshold and gy <= threshold:
                    a, b = groups[i]["bbox"], groups[j]["bbox"]
                    groups[i]["bbox"] = [
                        min(a[0], b[0]), min(a[1], b[1]),
                        max(a[2], b[2]), max(a[3], b[3])
                    ]
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break

    return [(g["label"], g["bbox"], "normalized_1000") for g in groups] + passthrough


def _relative_region(answer):
    text = re.sub(r"\s+", " ", (answer or "").lower())
    patterns = (
        (r"\bupper[\s-]+left\b|\btop[\s-]+left\b", "upper-left"),
        (r"\bupper[\s-]+right\b|\btop[\s-]+right\b", "upper-right"),
        (r"\blower[\s-]+left\b|\bbottom[\s-]+left\b", "lower-left"),
        (r"\blower[\s-]+right\b|\bbottom[\s-]+right\b", "lower-right"),
        (r"\bcenter(?:ed)?\b|\bcentral\b|\bmiddle\b", "center"),
        (r"\bleft(?:\s+side)?\b", "left"),
        (r"\bright(?:\s+side)?\b", "right"),
        (r"\bupper\b|\btop\b", "upper"),
        (r"\blower\b|\bbottom\b", "lower"),
    )
    for pattern, key in patterns:
        if re.search(pattern, text):
            return key, RELATIVE_REGION_BBOXES[key]
    return None


def _target_label(query):
    text = re.sub(
        r"\b(where|is|are|the|a|an|please|highlight|locate|location|find|show|me|mark|detect|identify|in|on|this|image|satellite|area|areas)\b",
        " ",
        query or "",
        flags=re.I,
    )
    return re.sub(r"\s+", " ", text).strip(" ?.,")[:80] or "Requested feature"


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
                    "bbox_space": "pixel",
                },
                "geometry": None,
            }
        except Exception:
            return None


def _read_rgb(file_bytes, max_side=1200):
    with rasterio.MemoryFile(file_bytes) as mem:
        with mem.open() as src:
            if src.count < 3:
                return None, src.width, src.height

            scale = min(1.0, max_side / max(src.width, src.height))
            h = max(1, int(src.height * scale))
            w = max(1, int(src.width * scale))

            data = src.read(
                [1, 2, 3],
                out_shape=(3, h, w),
                resampling=rasterio.enums.Resampling.bilinear,
                masked=True,
            ).astype(np.float32)

            return np.ma.filled(data, np.nan), src.width, src.height


def _normalize(rgb):
    out = []
    for channel in rgb:
        finite = channel[np.isfinite(channel)]
        if finite.size == 0:
            out.append(np.zeros_like(channel))
            continue
        lo, hi = np.percentile(finite, [2, 98])
        out.append(
            np.zeros_like(channel)
            if hi <= lo
            else np.clip((channel - lo) / (hi - lo), 0, 1)
        )
    return np.stack(out)


def _dilate(mask, radius=2):
    result = mask.copy()
    for _ in range(radius):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        result = (
            padded[:-2, :-2] | padded[:-2, 1:-1] | padded[:-2, 2:] |
            padded[1:-1, :-2] | padded[1:-1, 1:-1] | padded[1:-1, 2:] |
            padded[2:, :-2] | padded[2:, 1:-1] | padded[2:, 2:]
        )
    return result


def _erode(mask, radius=1):
    result = mask.copy()
    for _ in range(radius):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        result = (
            padded[:-2, :-2] & padded[:-2, 1:-1] & padded[:-2, 2:] &
            padded[1:-1, :-2] & padded[1:-1, 1:-1] & padded[1:-1, 2:] &
            padded[2:, :-2] & padded[2:, 1:-1] & padded[2:, 2:]
        )
    return result


def _water_mask(rgb):
    r, g, b = _normalize(rgb)
    brightness = (r + g + b) / 3
    blue_advantage = b - r
    cyan_advantage = ((g + b) / 2) - r
    vegetation = (g > r + 0.07) & (g > b + 0.025)

    mask = (
        (brightness < 0.62)
        & ~vegetation
        & (
            ((blue_advantage > 0.035) & (b > 0.24))
            | ((cyan_advantage > 0.045) & (g > 0.22) & (b > 0.24))
        )
    )
    return _erode(_dilate(mask, 1), 1)


def _vegetation_mask(rgb, forest=False):
    r, g, b = _normalize(rgb)
    brightness = (r + g + b) / 3
    green_advantage = g - np.maximum(r, b)
    saturation = np.max(np.stack([r, g, b]), axis=0) - np.min(np.stack([r, g, b]), axis=0)

    # Forest/vegetation is treated as a visual RGB evidence layer, not as a
    # trained land-cover classifier. Forest is biased toward larger, darker,
    # greener contiguous regions than general vegetation.
    if forest:
        mask = (
            (green_advantage > 0.045)
            & (saturation > 0.08)
            & (brightness > 0.10)
            & (brightness < 0.72)
        )
    else:
        mask = (
            (green_advantage > 0.035)
            & (saturation > 0.06)
            & (brightness > 0.08)
            & (brightness < 0.82)
        )
    return _erode(_dilate(mask, 1), 1)


def _builtup_mask(rgb):
    r, g, b = _normalize(rgb)
    brightness = (r + g + b) / 3
    saturation = np.max(np.stack([r, g, b]), axis=0) - np.min(np.stack([r, g, b]), axis=0)
    green_advantage = g - np.maximum(r, b)

    # Urban/built-up regions in RGB previews are commonly bright and relatively
    # neutral. Vegetation and very dark water are explicitly excluded.
    mask = (
        (brightness > 0.40)
        & (saturation < 0.23)
        & (green_advantage < 0.055)
    )
    return _erode(_dilate(mask, 1), 1)


def _bare_mask(rgb):
    r, g, b = _normalize(rgb)
    brightness = (r + g + b) / 3
    saturation = np.max(np.stack([r, g, b]), axis=0) - np.min(np.stack([r, g, b]), axis=0)
    warm = r - b
    green_advantage = g - np.maximum(r, b)

    mask = (
        (brightness > 0.42)
        & (saturation < 0.30)
        & (warm > -0.015)
        & (green_advantage < 0.05)
    )
    return _erode(_dilate(mask, 1), 1)


def _road_mask(rgb):
    r, g, b = _normalize(rgb)
    brightness = (r + g + b) / 3
    saturation = np.max(np.stack([r, g, b]), axis=0) - np.min(np.stack([r, g, b]), axis=0)

    mask = (
        (brightness > 0.35)
        & (brightness < 0.88)
        & (saturation < 0.18)
    )
    return _erode(_dilate(mask, 1), 1)


def _components(mask, min_area):
    h, w = mask.shape
    parent = np.arange(h * w, dtype=np.int32)
    size = np.ones(h * w, dtype=np.int32)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        p = y * w + x
        if x > 0 and mask[y, x - 1]:
            union(p, p - 1)
        if y > 0 and mask[y - 1, x]:
            union(p, p - w)

    boxes = {}
    for y, x in zip(ys, xs):
        root = find(y * w + x)
        if root not in boxes:
            boxes[root] = [0, x, y, x, y]
        item = boxes[root]
        item[0] += 1
        item[1] = min(item[1], x)
        item[2] = min(item[2], y)
        item[3] = max(item[3], x)
        item[4] = max(item[4], y)

    return [v for v in boxes.values() if v[0] >= min_area]


def _box_iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1, (a[2] - a[0]) * (a[3] - a[1]))
    area_b = max(1, (b[2] - b[0]) * (b[3] - b[1]))
    return inter / (area_a + area_b - inter)


def _target_from_query(query):
    q = re.sub(r"[^a-z0-9+\s-]", " ", (query or "").lower())
    # Prefer the feature that is the grammatical object of the request.
    # This matters for queries such as "built-up areas near the water", where
    # water is context but built-up is the feature that must be highlighted.
    if re.search(r"\b(shoreline|shore|coastline)\b", q):
        return "shoreline"
    if re.search(r"\b(forest|woodland|tree|trees|wooded)\b", q):
        return "forest"
    if re.search(r"\b(building|buildings|built-up|built up|urban|city|settlement|residential|developed)\b", q):
        return "built_up"
    if re.search(r"\b(vegetation|vegetated|green area|greenery|plants|crops|crop|agriculture|agricultural|farmland)\b", q):
        return "vegetation"
    if re.search(r"\b(road|roads|highway|street|route)\b", q):
        return "road"
    if re.search(r"\b(bare land|bare ground|sand|sandy|soil|desert)\b", q):
        return "bare"
    if re.search(r"\b(water|lake|river|sea|ocean|reservoir|pond|canal|coast)\b", q):
        return "water"
    if re.search(r"\b(road|roads|highway|street|route)\b", q):
        return "road"
    if re.search(r"\b(bare land|bare ground|sand|sandy|soil|desert)\b", q):
        return "bare"
    return None


def _mask_for_target(rgb, target):
    if target == "water":
        return _water_mask(rgb)
    if target == "forest":
        return _vegetation_mask(rgb, forest=True)
    if target == "vegetation":
        return _vegetation_mask(rgb, forest=False)
    if target == "built_up":
        return _builtup_mask(rgb)
    if target == "road":
        return _road_mask(rgb)
    if target == "bare":
        return _bare_mask(rgb)
    return None


def _relative_roi_mask(shape, relative):
    if not relative:
        return None
    _, bbox = relative
    h, w = shape
    x1, y1, x2, y2 = bbox
    px1, px2 = int(w * x1 / 1000), int(w * x2 / 1000)
    py1, py2 = int(h * y1 / 1000), int(h * y2 / 1000)
    roi = np.zeros(shape, dtype=bool)
    roi[max(0, py1):min(h, py2), max(0, px1):min(w, px2)] = True
    return roi


def _candidate_bboxes(mask, relative=None, max_components=8):
    min_area = max(80, int(mask.size * 0.0015))
    comps = _components(mask, min_area)
    if not comps:
        return []

    h, w = mask.shape
    candidates = []
    roi = _relative_roi_mask(mask.shape, relative)

    for c in comps:
        area, x1, y1, x2, y2 = c
        box = [float(x1), float(y1), float(x2 + 1), float(y2 + 1)]
        box_area = max(1, (x2 - x1 + 1) * (y2 - y1 + 1))
        fill = area / box_area
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

        roi_overlap = 1.0
        if roi is not None:
            rx = max(0, min(w - 1, int(cx)))
            ry = max(0, min(h - 1, int(cy)))
            roi_overlap = 1.0 if roi[ry, rx] else 0.0

        candidates.append({
            "area": area,
            "box": box,
            "fill": fill,
            "center": (cx / max(1, w), cy / max(1, h)),
            "roi": roi_overlap,
        })

    # If EarthDial supplied a relative location, prefer components whose center
    # falls inside that region. If none do, keep the global candidates instead.
    in_roi = [c for c in candidates if c["roi"] > 0]
    pool = in_roi if in_roi else candidates
    pool.sort(key=lambda c: (c["area"] * (0.75 + 0.25 * c["fill"])), reverse=True)
    return [c["box"] for c in pool[:max_components]]


def _merge_pixel_bboxes(boxes, image_width, image_height, gap_normalized=65.0):
    if not boxes:
        return []

    sx = 1000.0 / max(1, image_width)
    sy = 1000.0 / max(1, image_height)
    groups = [{
        "bbox": [
            max(0.0, min(1000.0, b[0] * sx)),
            max(0.0, min(1000.0, b[1] * sy)),
            max(0.0, min(1000.0, b[2] * sx)),
            max(0.0, min(1000.0, b[3] * sy)),
        ]
    } for b in boxes]

    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                gx, gy = _gap(groups[i]["bbox"], groups[j]["bbox"])
                if gx <= gap_normalized and gy <= gap_normalized:
                    a, b = groups[i]["bbox"], groups[j]["bbox"]
                    groups[i]["bbox"] = [
                        min(a[0], b[0]), min(a[1], b[1]),
                        max(a[2], b[2]), max(a[3], b[3]),
                    ]
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break

    return [[
        g["bbox"][0] / sx,
        g["bbox"][1] / sy,
        g["bbox"][2] / sx,
        g["bbox"][3] / sy,
    ] for g in groups]


def _visual_grounding_fallback(file_bytes, query, relative=None):
    target = _target_from_query(query)
    if target is None or target == "shoreline":
        return [], None

    rgb, original_w, original_h = _read_rgb(file_bytes)
    if rgb is None:
        return [], target

    mask = _mask_for_target(rgb, target)
    if mask is None:
        return [], target

    boxes = _candidate_bboxes(mask, relative=relative, max_components=8)
    if not boxes:
        return [], target

    merge_gap = {
        "water": 65.0,
        "forest": 45.0,
        "vegetation": 40.0,
        "built_up": 45.0,
        "road": 28.0,
        "bare": 40.0,
    }.get(target, 40.0)

    boxes = _merge_pixel_bboxes(
        boxes,
        image_width=original_w,
        image_height=original_h,
        gap_normalized=merge_gap,
    )

    return boxes, target


def _visual_water_fallback(file_bytes, query):
    boxes, target = _visual_grounding_fallback(file_bytes, query)
    if target != "water":
        return []
    return [{
        "type": "Feature",
        "properties": {
            "label": _target_label(query),
            "bbox_pixel": bbox,
            "bbox_space": "pixel",
            "evidence_source": "raster_visual_fallback",
            "approximate": True,
            "relative_location": "raster-detected",
        },
        "geometry": None,
    } for bbox in boxes]


def _visual_feature_fallback(file_bytes, query, relative):
    boxes, target = _visual_grounding_fallback(file_bytes, query, relative=relative)
    if not boxes:
        return [], target

    return [{
        "type": "Feature",
        "properties": {
            "label": _target_label(query),
            "bbox_pixel": bbox,
            "bbox_space": "pixel",
            "evidence_source": "raster_visual_fallback",
            "approximate": True,
            "relative_location": "raster-detected" if relative is None else relative[0],
            "target_class": target,
        },
        "geometry": None,
    } for bbox in boxes], target


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
    relative = _relative_region(answer)

    # First visual fallback: use the actual uploaded raster instead of turning
    # a relative answer into a generic 50% quadrant. This now supports water,
    # forest/vegetation, built-up areas, roads and bare land.
    if not features:
        visual_features, visual_target = _visual_feature_fallback(
            file_bytes, query, relative
        )
        if visual_features:
            features = visual_features
            evidence_source = "raster_visual_fallback"

    # Keep the existing highly useful water-specific path for compatibility.
    if not features:
        visual_features = _visual_water_fallback(file_bytes, query)
        if visual_features:
            features = visual_features
            evidence_source = "raster_visual_fallback"

    # Last resort: use EarthDial's relative-location statement. This remains
    # available for targets that cannot be separated reliably from RGB pixels.
    if not features and relative:
        key, bbox = relative
        try:
            pixel_bbox = normalize_bbox_to_pixel(file_bytes, bbox, "normalized_1000")
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
        "confidence": estimate_confidence("grounding", answer, spatial_features=len(features)),
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
