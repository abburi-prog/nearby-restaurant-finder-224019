# Nearby Restaurant Finder - Backend (FastAPI)

FastAPI backend providing restaurant search endpoints.
Defaults to Delhi, India when coordinates are absent and applies region bias 'IN' and language 'en-IN'.
No external API keys are required for this demo implementation.

## Run

pip install fastapi uvicorn pydantic
uvicorn main:app --host 0.0.0.0 --port 3001

## Endpoints

- GET / : Health check
- POST /api/restaurants/nearby : Nearby search, defaults to Delhi if no lat/lng provided. Accepts {lat?, lng?, radius?, keyword?, region?, language?}
- GET /api/restaurants/{place_id} : Sample place details

OpenAPI docs at /docs
