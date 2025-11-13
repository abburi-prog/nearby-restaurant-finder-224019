# Nearby Restaurant Finder - Backend (FastAPI)

FastAPI backend that proxies Google Places APIs to avoid exposing API keys to the frontend. Provides:
- GET /api/health
- POST /api/restaurants/nearby
- GET /api/restaurants/{place_id}

## Environment Variables

Copy `.env.example` and provide real values at runtime:

- GOOGLE_MAPS_API_KEY: Backend Google Maps Platform API key (Places API enabled)
- REACT_APP_FRONTEND_URL: Frontend origin for CORS (e.g., http://localhost:3000)

## Setup

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 3001

## Security

- Do not commit real secrets.
- All outgoing requests to Google are server-side.
- Input validated and sanitized.

