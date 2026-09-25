from app.services.kaggle_client import infer

def run(file_tuple, query: str):
    result = infer(file_tuple, query, "[caption]")
    return {
        "answer": str(result.get("answer", "")),
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": 0.80,
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {"tag": result.get("tag", "[caption]")},
    }
