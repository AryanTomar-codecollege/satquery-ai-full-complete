from io import BytesIO

import numpy as np
import rasterio
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from rasterio.io import MemoryFile

router = APIRouter(prefix="/api")


def _stretch(arr):
    arr = arr.astype("float32")
    finite = np.isfinite(arr)
    if not finite.any():
        return np.zeros(arr.shape, dtype=np.uint8)
    values = arr[finite]
    lo, hi = np.percentile(values, [2, 98])
    if hi <= lo:
        lo, hi = float(values.min()), float(values.max())
    if hi <= lo:
        return np.zeros(arr.shape, dtype=np.uint8)
    return np.clip((arr - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


@router.post("/preview")
async def preview(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        from PIL import Image
        with MemoryFile(data) as mem:
            with mem.open() as src:
                if src.count >= 3:
                    bands = src.read([1, 2, 3])
                    rgb = np.stack([_stretch(bands[0]), _stretch(bands[1]), _stretch(bands[2])], axis=-1)
                else:
                    band = _stretch(src.read(1))
                    rgb = np.stack([band, band, band], axis=-1)
                image = Image.fromarray(rgb, mode="RGB")
                max_side = 1400
                if max(image.size) > max_side:
                    scale = max_side / max(image.size)
                    image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
                output = BytesIO()
                image.save(output, format="PNG", optimize=True)
                return Response(content=output.getvalue(), media_type="image/png")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not create GeoTIFF preview: {exc}") from exc
