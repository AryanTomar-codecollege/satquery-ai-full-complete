from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExecutionTrace(BaseModel):
    selected_task: str
    tools_used: List[str] = Field(default_factory=list)
    model_used: str | None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    router: str = "deterministic"
    router_reason: str = ""

class Metadata(BaseModel):
    num_images: int
    modalities: List[str]
    crs: Optional[str] = None

class Report(BaseModel):
    title: str
    query: str
    timestamp: str
    tool: str
    model_used: str
    answer: str
    confidence: float
    execution_trace: Dict[str, Any]
    metadata: Dict[str, Any]
    geojson_feature_count: int

class QuerySuccess(BaseModel):
    success: bool = True
    answer: str
    geojson: Dict[str, Any]
    confidence: float
    execution_trace: ExecutionTrace
    metadata: Metadata
    report: Report

class QueryError(BaseModel):
    success: bool = False
    error: str
    error_code: str
