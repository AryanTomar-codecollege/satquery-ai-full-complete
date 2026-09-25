# SatQuery AI — SIH 26167 Backend

Student-readable FastAPI backend for the SatQuery AI prototype.

Architecture:

React frontend -> FastAPI -> validation/geospatial -> deterministic agent -> tools -> EarthDial_4B_MS on Kaggle via Ngrok.

Features:
- Single-image VQA
- Captioning
- Text-guided grounding with GeoJSON when parseable boxes are returned
- Bi-temporal change detection
- Optical + SAR dedicated path
- Metadata inspection
- GeoTIFF compatibility and geographic-overlap checks
- Fixed success/error response contract
- Execution trace and report
- EarthDial health endpoint
- USE_LORA=false hook only; no LoRA training

The local backend uses Python 3.11 and `.venv`. The supplied EarthDial Kaggle service uses its own Python 3.9 environment.
