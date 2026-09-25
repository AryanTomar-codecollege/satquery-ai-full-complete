# SatQuery AI — Full Stack

Integrated SIH 26167 project containing the existing FastAPI backend and existing React frontend.

## Run order

1. Start the existing Kaggle EarthDial notebook and obtain the Ngrok URL.
2. Configure `backend/.env` with the Kaggle URL and optional OmniRoute settings.
3. Start the backend on port `8001`.
4. Configure `frontend/.env` with `VITE_API_BASE_URL=http://127.0.0.1:8001`.
5. Start the frontend with `npm run dev`.

See `RUN.md` for the complete commands and acceptance tests.

## Important

The Kaggle EarthDial service was intentionally left unchanged in this integration.
