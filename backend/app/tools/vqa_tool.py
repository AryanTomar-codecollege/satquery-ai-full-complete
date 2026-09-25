from app.services.kaggle_client import infer
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_vqa_prompt

def run(file_tuple, query: str):
    result = infer(file_tuple, build_vqa_prompt(query), "[vqa]")
    answer = str(result.get("answer", "")).strip()
    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": estimate_confidence("vqa", answer),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {"tag": result.get("tag", "[vqa]")},
    }
