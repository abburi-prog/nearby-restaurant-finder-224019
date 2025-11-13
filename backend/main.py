from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import os
import httpx

APP_TITLE = "Nearby Restaurant Finder API"
APP_DESCRIPTION = "FastAPI backend that proxies Google Places endpoints to keep API keys server-side. Provides health, nearby search, and place details."
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, version=APP_VERSION,
              openapi_tags=[
                  {"name": "health", "description": "Service health status"},
                  {"name": "restaurants", "description": "Restaurant search and details via Google Places"}
              ])

# CORS setup using env var to restrict origins
frontend_origin = os.getenv("REACT_APP_FRONTEND_URL") or os.getenv("FRONTEND_URL")
allow_origins = [frontend_origin] if frontend_origin else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NearbyRequest(BaseModel):
    """Request payload for nearby restaurants."""
    lat: float = Field(..., description="Latitude of the search center")
    lng: float = Field(..., description="Longitude of the search center")
    radius: int = Field(1500, description="Search radius in meters (max 50000)")
    keyword: Optional[str] = Field(None, description="Optional keyword like cuisine or name")

    @validator("radius")
    def radius_bounds(cls, v: int) -> int:
        if v <= 0 or v > 50000:
            raise ValueError("radius must be between 1 and 50000")
        return v


class Restaurant(BaseModel):
    place_id: str
    name: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    vicinity: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    open_now: Optional[bool] = None
    distance_meters: Optional[float] = None  # Not computed here; client may compute


class NearbyResponse(BaseModel):
    results: List[Restaurant]
    next_page_token: Optional[str] = None


class PlaceDetailsResponse(BaseModel):
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    international_phone_number: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    opening_hours: Optional[dict] = None
    website: Optional[str] = None
    url: Optional[str] = None
    geometry: Optional[dict] = None


def _get_api_key() -> str:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Backend missing GOOGLE_MAPS_API_KEY env variable")
    return api_key


# PUBLIC_INTERFACE
@app.get("/api/health", tags=["health"], summary="Health Check", description="Returns service health status.")
def health():
    """Health check endpoint returning service status and config hints."""
    return {"status": "ok", "version": APP_VERSION, "cors_origin": allow_origins}


# PUBLIC_INTERFACE
@app.post("/api/restaurants/nearby", response_model=NearbyResponse, tags=["restaurants"],
          summary="Nearby restaurants", description="Search nearby restaurants using Google Places Nearby Search.")
async def nearby_restaurants(req: NearbyRequest):
    """Proxy Google Places Nearby Search. Requires GOOGLE_MAPS_API_KEY on the server.
    Parameters:
    - lat: float
    - lng: float
    - radius: int (1-50000)
    - keyword: optional string
    Returns: list of simplified restaurant objects and next_page_token when available.
    """
    api_key = _get_api_key()
    params = {
        "key": api_key,
        "location": f"{req.lat},{req.lng}",
        "radius": str(req.radius),
        "type": "restaurant",
    }
    if req.keyword:
        # basic sanitization: strip and limit length
        kw = req.keyword.strip()
        if len(kw) > 80:
            kw = kw[:80]
        params["keyword"] = kw

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to query Google Places")

        data = r.json()
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS", "OVER_QUERY_LIMIT", "INVALID_REQUEST", "REQUEST_DENIED", "UNKNOWN_ERROR"):
            raise HTTPException(status_code=502, detail="Unexpected response from Google Places")

        results = data.get("results", [])
        simplified = []
        for item in results:
            geom = item.get("geometry", {}).get("location", {})
            simplified.append(Restaurant(
                place_id=item.get("place_id", ""),
                name=item.get("name", "Unknown"),
                rating=item.get("rating"),
                user_ratings_total=item.get("user_ratings_total"),
                vicinity=item.get("vicinity"),
                lat=geom.get("lat"),
                lng=geom.get("lng"),
                open_now=item.get("opening_hours", {}).get("open_now") if item.get("opening_hours") else None,
            ))
        return NearbyResponse(
            results=simplified,
            next_page_token=data.get("next_page_token")
        )


# PUBLIC_INTERFACE
@app.get("/api/restaurants/{place_id}", response_model=PlaceDetailsResponse, tags=["restaurants"],
         summary="Restaurant details", description="Get details for a restaurant place_id using Google Place Details.")
async def restaurant_details(place_id: str = Query(..., min_length=1, max_length=128)):
    """Proxy Google Place Details. Returns a curated subset of fields."""
    # Basic validation: prevent path traversal-like inputs
    if "/" in place_id or "\\" in place_id:
        raise HTTPException(status_code=400, detail="Invalid place_id format")

    api_key = _get_api_key()
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,international_phone_number,rating,user_ratings_total,opening_hours,website,url,geometry",
    }
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to query Google Place Details")
        data = r.json()
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS", "OVER_QUERY_LIMIT", "INVALID_REQUEST", "REQUEST_DENIED", "UNKNOWN_ERROR"):
            raise HTTPException(status_code=502, detail="Unexpected response from Google Place Details")

        result = data.get("result", {}) or {}
        return PlaceDetailsResponse(
            place_id=result.get("place_id", place_id),
            name=result.get("name", "Unknown"),
            formatted_address=result.get("formatted_address"),
            international_phone_number=result.get("international_phone_number"),
            rating=result.get("rating"),
            user_ratings_total=result.get("user_ratings_total"),
            opening_hours=result.get("opening_hours"),
            website=result.get("website"),
            url=result.get("url"),
            geometry=result.get("geometry"),
        )


# Root redirect/help
@app.get("/", include_in_schema=False)
def root_help():
    """Basic index route redirecting users to API docs."""
    return {"message": "Nearby Restaurant Finder API. Visit /docs for OpenAPI UI."}
