from app.services.kaggle_client import infer_multi

def run(files_data, query: str):
    result = infer_multi(files_data, query, "[optical_sar]")
    return {
        "answer": str(result.get("answer", "")),
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": 0.72,
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[optical_sar]"),
            "file_count": result.get("file_count", len(files_data)),
        },
    }
