from app.services.kaggle_client import infer
from app.services.confidence import estimate_confidence
from app.services.prompt_builder import build_caption_prompt
from app.services.spatial_evidence import geojson_from_answer

def run(file_tuple, query: str = ""):
    result = infer(file_tuple, build_caption_prompt(query), "[caption]")
    answer = str(result.get("answer", "")).strip()
    geojson = geojson_from_answer(file_tuple[1], answer)
    return {"answer": answer, "geojson": geojson, "confidence": estimate_confidence("caption", answer, spatial_features=len(geojson["features"])), "model_used": result.get("model", "EarthDial_4B_MS"), "parameters": {"tag": result.get("tag", "[caption]"), "boxes_parsed": len(geojson["features"])} }
