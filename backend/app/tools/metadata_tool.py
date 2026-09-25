from app.services.geospatial import inspect

def run(data: bytes, filename: str):
    meta = inspect(data, filename)
    return {
        "answer": (
            f"{filename}: {meta['width']}x{meta['height']} pixels, "
            f"{meta['bands']} band(s), CRS={meta['crs']}, dtype={meta['dtype']}."
        ),
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": 1.0,
        "model_used": "local-geospatial-inspection",
        "parameters": {"filename": filename},
    }
