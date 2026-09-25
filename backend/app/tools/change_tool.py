from app.services.kaggle_client import infer_multi
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_change_prompt

def run(files_data, query: str):
    result = infer_multi(files_data, build_change_prompt(query), "[changedet]")
    answer = str(result.get("answer", "")).strip()
    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": estimate_confidence("change", answer),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[changedet]"),
            "file_count": result.get("file_count", len(files_data)),
        },
    }
