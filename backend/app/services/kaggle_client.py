from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import httpx

from app.config import EARTHDIAL_MODEL, KAGGLE_NGROK_URL, REQUEST_TIMEOUT, kaggle_url_configured

class EarthDialError(Exception):
    pass

def configured() -> bool:
    return kaggle_url_configured()

def _headers():
    return {"ngrok-skip-browser-warning": "true"}

def health() -> Optional[Dict]:
    if not configured():
        return None
    try:
        r = httpx.get(
            KAGGLE_NGROK_URL.rstrip("/") + "/health",
            headers=_headers(),
            timeout=min(15.0, REQUEST_TIMEOUT),
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def _body_or_error(response: httpx.Response) -> Dict:
    try:
        body = response.json()
    except Exception as exc:
        raise EarthDialError(
            f"EarthDial returned non-JSON HTTP {response.status_code}."
        ) from exc
    if body.get("success") is False:
        raise EarthDialError(body.get("error", "EarthDial request failed."))
    if response.status_code >= 500:
        raise EarthDialError(body.get("error", "EarthDial server error."))
    return body

def infer(file_tuple: Tuple[str, bytes, str], query: str, tag: str) -> Dict:
    if not configured():
        raise EarthDialError(
            "EarthDial is unavailable: KAGGLE_NGROK_URL is not configured."
        )
    filename, contents, content_type = file_tuple
    try:
        r = httpx.post(
            KAGGLE_NGROK_URL.rstrip("/") + "/infer",
            headers=_headers(),
            files={"file": (filename, contents, content_type or "image/tiff")},
            data={"query": query, "tag": tag},
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise TimeoutError("EarthDial single-image inference timed out.") from exc
    except httpx.HTTPError as exc:
        raise EarthDialError(f"EarthDial connection failed: {exc}") from exc
    return _body_or_error(r)

def infer_multi(files_data: List[Tuple[str, bytes, str]], query: str, tag: str) -> Dict:
    if not configured():
        raise EarthDialError(
            "EarthDial is unavailable: KAGGLE_NGROK_URL is not configured."
        )
    files = [
        ("files", (name, data, content_type or "image/tiff"))
        for name, data, content_type in files_data
    ]
    try:
        r = httpx.post(
            KAGGLE_NGROK_URL.rstrip("/") + "/infer_multi",
            headers=_headers(),
            files=files,
            data={"query": query, "tag": tag},
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise TimeoutError("EarthDial multi-image inference timed out.") from exc
    except httpx.HTTPError as exc:
        raise EarthDialError(f"EarthDial connection failed: {exc}") from exc
    return _body_or_error(r)
