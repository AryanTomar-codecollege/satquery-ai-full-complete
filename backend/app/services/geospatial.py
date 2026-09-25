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
        b["left"], b["bottom"], b["right"], b["top"],
        densify_pts=21,
    )

def metadata_boxes_overlap(meta_a: Dict[str, Any], meta_b: Dict[str, Any]) -> bool:
    if not meta_a.get("crs") or not meta_b.get("crs"):
        return boxes_overlap(meta_a["bounds"], meta_b["bounds"])
    a = meta_a["bounds"]
    x1, y1, x2, y2 = _bounds_in_crs(meta_b, meta_a["crs"])
    return boxes_overlap(a, {"left": x1, "bottom": y1, "right": x2, "top": y2})

def _pixel_bbox_to_geo_bounds(data: bytes, bbox: Iterable[float], space: str):
    values = [float(x) for x in bbox]
    if len(values) != 4:
        raise ValueError("bbox must contain [x1, y1, x2, y2].")
    x1, y1, x2, y2 = values

    with MemoryFile(data) as mem:
        with mem.open() as src:
            if space == "pixel":
                px1, py1, px2, py2 = x1, y1, x2, y2
            elif space == "normalized_1":
                px1, py1 = x1 * src.width, y1 * src.height
                px2, py2 = x2 * src.width, y2 * src.height
            elif space == "normalized_1000":
                px1, py1 = (x1 / 1000) * src.width, (y1 / 1000) * src.height
                px2, py2 = (x2 / 1000) * src.width, (y2 / 1000) * src.height
            else:
                raise ValueError("space must be pixel, normalized_1, or normalized_1000")

            px1 = max(0.0, min(float(src.width), px1))
            px2 = max(0.0, min(float(src.width), px2))
            py1 = max(0.0, min(float(src.height), py1))
            py2 = max(0.0, min(float(src.height), py2))
            left, right = sorted((px1, px2))
            top, bottom = sorted((py1, py2))

            points = [
                rasterio.transform.xy(src.transform, row, col, offset="center")
                for row, col in [
                    (top, left), (top, right), (bottom, left), (bottom, right)
                ]
            ]
            xs, ys = zip(*points)
            return min(xs), min(ys), max(xs), max(ys)

def pixel_bbox_to_geojson_feature(data: bytes, bbox: Iterable[float], space: str = "pixel"):
    left, bottom, right, top = _pixel_bbox_to_geo_bounds(data, bbox, space)
    with MemoryFile(data) as mem:
        with mem.open() as src:
            return {
                "type": "Feature",
                "properties": {
                    "bbox_space": space,
                    "crs": src.crs.to_string() if src.crs else None,
                },
                "geometry": mapping(box(left, bottom, right, top)),
            }
