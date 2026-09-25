# SatQuery AI Setup

## Local

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

After Kaggle is online, put its printed URL into `.env`:

```env
KAGGLE_NGROK_URL=https://YOUR_REAL_NGROK_URL
```

Useful endpoints:
- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/api/model/health`
- `http://127.0.0.1:8001/docs`

## Kaggle

1. Create a Kaggle Notebook.
2. Turn Internet ON.
3. Turn GPU ON and use a T4 if available.
4. Create and attach the Kaggle Secret `NGROK_AUTHTOKEN`.
5. Run `kaggle/earthdial_kaggle_service.py`.
6. Wait for `STATUS: ONLINE`.
7. Copy the printed `KAGGLE_NGROK_URL=...` to the local `.env`.
8. Keep the Kaggle session running.

## Six tests

1. Metadata: one TIFF, `Show the CRS, dimensions and band count.`, `task_hint=metadata`.
2. VQA: one TIFF, `What major land-cover features are visible?`, `task_hint=vqa`.
3. Grounding: one TIFF, `Locate the buildings and return bounding boxes.`, `task_hint=grounding`.
4. Change: two overlapping TIFFs, `What changed between the two images?`, `task_hint=change`.
5. Optical/SAR: one optical + one SAR overlapping TIFF, `Compare the optical and SAR observations.`, `task_hint=optical_sar`.
6. Geographic mismatch: two valid non-overlapping TIFFs; expect `error_code=GEOGRAPHIC_MISMATCH`.

Example:

```bash
curl -X POST "http://127.0.0.1:8001/api/query" ^
  -F "files=@sample.tif" ^
  -F "query=Describe the main land-cover features." ^
  -F "task_hint=caption"
```
