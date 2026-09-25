from app.services.kaggle_client import infer_multi

def run(files_data, query: str):
    result = infer_multi(files_data, query, "[changedet]")
    return {
        "answer": str(result.get("answer", "")),
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": 0.74,
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[changedet]"),
            "file_count": result.get("file_count", len(files_data)),
        },
    }
