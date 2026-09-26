from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import transform_bounds
from shapely.geometry import box, mapping


def inspect(data: bytes, filename: str = "image.tif") -> Dict[str, Any]:
    if not data:
        raise ValueError("Uploaded file is empty.")
    try:
        with MemoryFile(data) as mem:
            with mem.open() as src:
                bounds = {
                    "left": float(src.bounds.left),
                    "bottom": float(src.bounds.bottom),
                    "right": float(src.bounds.right),
                    "top": float(src.bounds.top),
                }
                return {
                    "filename": filename,
                    "width": int(src.width),
                    "height": int(src.height),
                    "bands": int(src.count),
                    "crs": src.crs.to_string() if src.crs else None,
                    "bounds": bounds,
                    "dtype": str(src.dtypes[0]) if src.dtypes else None,
                    "descriptions": list(src.descriptions),
                }
    except Exception as exc:
        raise ValueError(f"Could not read GeoTIFF: {exc}") from exc


def estimate_modality(meta: Dict[str, Any], filename: str = "") -> str:
    text = " ".join([
        filename or "",
        str(meta.get("filename", "")),
        " ".join(str(x or "") for x in meta.get("descriptions", [])),
    ]).lower()
    sar_terms = ("sar", "sentinel-1", "sentinel1", "c-band", "vv", "vh",
                 "hh", "hv", "sigma0", "backscatter", "radar")
    optical_terms = ("optical", "sentinel-2", "sentinel2", "landsat",
                     "multispectral", "red", "green", "blue", "nir", "swir")
    if any(x in text for x in sar_terms):
        return "sar"
    if any(x in text for x in optical_terms):
        return "optical"
    return "optical" if int(meta.get("bands", 0) or 0) >= 3 else "unknown"


def boxes_overlap(bounds_a: Dict[str, float], bounds_b: Dict[str, float]) -> bool:
    return not (
        bounds_a["right"] <= bounds_b["left"]
        or bounds_b["right"] <= bounds_a["left"]
        or bounds_a["top"] <= bounds_b["bottom"]
        or bounds_b["top"] <= bounds_a["bottom"]
    )


def _bounds_in_crs(meta: Dict[str, Any], target_crs: str) -> Tuple[float, float, float, float]:
    b = meta["bounds"]
    if not meta.get("crs") or meta["crs"] == target_crs:
        return b["left"], b["bottom"], b["right"], b["top"]
    return transform_bounds(
        meta["crs"], target_crs,
        b["left"], b["bottom"], b["right"], b["top"], densify_pts=21,
    )


def metadata_boxes_overlap(meta_a: Dict[str, Any], meta_b: Dict[str, Any]) -> bool:
    if not meta_a.get("crs") or not meta_b.get("crs"):
        return boxes_overlap(meta_a["bounds"], meta_b["bounds"])
    a = meta_a["bounds"]
    x1, y1, x2, y2 = _bounds_in_crs(meta_b, meta_a["crs"])
    return boxes_overlap(a, {"left": x1, "bottom": y1, "right": x2, "top": y2})


def normalize_bbox_to_pixel(data: bytes, bbox: Iterable[float], space: str = "pixel") -> list[float]:
    values = [float(x) for x in bbox]
    if len(values) != 4:
        raise ValueError("bbox must contain [x1, y1, x2, y2].")
    with MemoryFile(data) as mem:
        with mem.open() as src:
            x1, y1, x2, y2 = values
            if space == "normalized_1":
                x1, x2 = x1 * src.width, x2 * src.width
                y1, y2 = y1 * src.height, y2 * src.height
            elif space == "normalized_1000":
                x1, x2 = (x1 / 1000) * src.width, (x2 / 1000) * src.width
                y1, y2 = (y1 / 1000) * src.height, (y2 / 1000) * src.height
            elif space != "pixel":
                raise ValueError("space must be pixel, normalized_1, or normalized_1000")
            x1 = max(0.0, min(float(src.width), x1))
            x2 = max(0.0, min(float(src.width), x2))
            y1 = max(0.0, min(float(src.height), y1))
            y2 = max(0.0, min(float(src.height), y2))
            return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]


def pixel_bbox_to_geojson_feature(data: bytes, bbox: Iterable[float], space: str = "pixel", label: str = "detected feature"):
    pixel_bbox = normalize_bbox_to_pixel(data, bbox, space)
    with MemoryFile(data) as mem:
        with mem.open() as src:
            px1, py1, px2, py2 = pixel_bbox
            points = [
                rasterio.transform.xy(src.transform, row, col, offset="center")
                for row, col in [(py1, px1), (py1, px2), (py2, px1), (py2, px2)]
            ]
            xs, ys = zip(*points)
            geometry = mapping(box(min(xs), min(ys), max(xs), max(ys)))
            return {
                "type": "Feature",
                "properties": {
                    "label": label,
                    "bbox_pixel": pixel_bbox,
                    "bbox_space": space,
                    "crs": src.crs.to_string() if src.crs else None,
                },
                "geometry": geometry,
            }
