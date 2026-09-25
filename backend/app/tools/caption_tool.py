from app.services.kaggle_client import infer
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_caption_prompt

def run(file_tuple, query: str = ""):
    result = infer(file_tuple, build_caption_prompt(query), "[caption]")
    answer = str(result.get("answer", "")).strip()
    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": estimate_confidence("caption", answer),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {"tag": result.get("tag", "[caption]")},
    }
