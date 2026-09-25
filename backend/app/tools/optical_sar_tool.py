from app.services.kaggle_client import infer_multi
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_optical_sar_prompt

def run(files_data, query: str):
    result = infer_multi(files_data, build_optical_sar_prompt(query), "[optical_sar]")
    answer = str(result.get("answer", "")).strip()
    return {
        "answer": answer,
        "geojson": {"type": "FeatureCollection", "features": []},
        "confidence": estimate_confidence("optical_sar", answer),
        "model_used": result.get("model", "EarthDial_4B_MS"),
        "parameters": {
            "tag": result.get("tag", "[optical_sar]"),
            "file_count": result.get("file_count", len(files_data)),
        },
    }
