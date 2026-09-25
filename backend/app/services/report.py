from datetime import datetime, timezone

def build_report(query, tool, model_used, answer, confidence, execution_trace, metadata, geojson):
    return {
        "title": "SatQuery AI Analysis Report",
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "model_used": model_used,
        "answer": answer,
        "confidence": confidence,
        "execution_trace": execution_trace,
        "metadata": metadata,
        "geojson_feature_count": len(geojson.get("features", [])),
    }
