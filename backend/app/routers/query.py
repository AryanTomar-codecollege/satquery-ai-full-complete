from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from typing import List

from app.config import MAX_FILES
from app.services import agent, geospatial
from app.services.kaggle_client import EarthDialError
from app.services.report import build_report

router = APIRouter(prefix="/api")

def _error(code, message):
    raise HTTPException(
        status_code=400,
        detail={"success": False, "error": message, "error_code": code},
    )

@router.post("/query")
async def query(
    files: List[UploadFile] = File(...),
    query: str = Form(...),
    task_hint: str = Form("auto"),
):
    if not query.strip():
        _error("EMPTY_QUERY", "Query cannot be empty.")
    if not files:
        _error("NO_FILES", "At least one GeoTIFF file is required.")
    if len(files) > MAX_FILES:
        _error("TOO_MANY_FILES", f"A maximum of {MAX_FILES} files is allowed.")
    if task_hint not in {"auto", "vqa", "caption", "grounding", "change", "optical_sar", "metadata"}:
        _error("INVALID_FORMAT", f"Unsupported task_hint: {task_hint}")

    files_data, metas = [], []

    for uploaded in files:
        filename = uploaded.filename or "upload.tif"
        if not filename.lower().endswith((".tif", ".tiff", ".geotiff")):
            _error("INVALID_FORMAT", f"{filename} is not a GeoTIFF/TIFF file.")
        data = await uploaded.read()
        try:
            meta = geospatial.inspect(data, filename)
        except ValueError as exc:
            _error("INVALID_FORMAT", str(exc))
        files_data.append((filename, data, uploaded.content_type or "image/tiff"))
        metas.append(meta)

    if len(metas) == 2:
        try:
            overlap = geospatial.metadata_boxes_overlap(metas[0], metas[1])
        except Exception as exc:
            _error("GEOGRAPHIC_MISMATCH", f"Could not compare image footprints: {exc}")
        if not overlap:
            _error(
                "GEOGRAPHIC_MISMATCH",
                "The two GeoTIFFs do not have an overlapping geographic footprint.",
            )

    try:
        result = agent.run(files_data, metas, query, task_hint)
    except TimeoutError as exc:
        _error("INFERENCE_TIMEOUT", str(exc))
    except EarthDialError as exc:
        _error("EARTHDIAL_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error("INFERENCE_FAILED", f"Analysis failed: {exc}")

    modalities = [
        geospatial.estimate_modality(meta, meta.get("filename", "")) for meta in metas
    ]
    crs_values = [meta.get("crs") for meta in metas if meta.get("crs")]
    metadata = {
        "num_images": len(metas),
        "modalities": modalities,
        "crs": crs_values[0] if crs_values else None,
    }

    report = build_report(
        query=query,
        tool=result["execution_trace"]["tools_used"][0],
        model_used=result["model_used"],
        answer=result["answer"],
        confidence=result["confidence"],
        execution_trace=result["execution_trace"],
        metadata=metadata,
        geojson=result["geojson"],
    )

    return {
        "success": True,
        "answer": result["answer"],
        "geojson": result["geojson"],
        "confidence": result["confidence"],
        "execution_trace": result["execution_trace"],
        "metadata": metadata,
        "report": report,
    }
