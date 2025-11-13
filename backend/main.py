from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class NearbySearchRequest(BaseModel):
    """Request body for nearby restaurant search."""
    lat: Optional[float] = Field(None, description="Latitude of the center point. Defaults to Delhi if omitted.")
    lng: Optional[float] = Field(None, description="Longitude of the center point. Defaults to Delhi if omitted.")
    radius: Optional[int] = Field(1500, description="Search radius in meters. Defaults to 1500.")
    keyword: Optional[str] = Field(None, description="Optional keyword to filter restaurants.")
    region: Optional[str] = Field(None, description="Region bias (e.g., 'IN'). Defaults to IN.")
    language: Optional[str] = Field(None, description="Language for results (e.g., 'en-IN'). Defaults to en-IN.")

# PUBLIC_INTERFACE
class Restaurant(BaseModel):
    """Restaurant item in results."""
    place_id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Restaurant name")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    rating: Optional[float] = Field(None, description="Average rating if available")
    vicinity: Optional[str] = Field(None, description="Address/vicinity")

# PUBLIC_INTERFACE
class NearbySearchResponse(BaseModel):
    """Nearby search response containing list of restaurants and applied bias info."""
    results: List[Restaurant]
    center: Dict[str, float]
    region: str
    language: str

app = FastAPI(
    title="Nearby Restaurant Finder Backend",
    description="Provides restaurant search endpoints. Defaults to Delhi, India when coordinates are absent and applies region bias 'IN'.",
    version="0.1.1",
    openapi_tags=[
        {"name": "restaurants", "description": "Restaurant discovery endpoints"},
        {"name": "health", "description": "Health and status endpoints"},
    ],
)

DELHI = {"lat": 28.6139, "lng": 77.2090}
DEFAULT_REGION = "IN"
DEFAULT_LANGUAGE = "en-IN"

# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

# PUBLIC_INTERFACE
@app.post(
    "/api/restaurants/nearby",
    response_model=NearbySearchResponse,
    tags=["restaurants"],
    summary="Nearby restaurants search",
    description="Performs a nearby search for restaurants. If lat/lng are not provided, defaults to Delhi, India. Region bias is set to 'IN' and language defaults to 'en-IN'. No Google API key required for this sample implementation.",
)
def nearby_search(req: NearbySearchRequest = Body(...)) -> NearbySearchResponse:
    """
    Perform a sample nearby restaurant search.

    Parameters:
    - lat/lng: optional; if omitted, defaults to Delhi (28.6139, 77.2090)
    - radius: optional meters, default 1500
    - keyword: optional filter
    - region: optional region bias, default 'IN'
    - language: optional language, default 'en-IN'

    Returns:
    - Sample list of restaurants around the computed center with region/language echoed.
    """
    center_lat = req.lat if req.lat is not None else DELHI["lat"]
    center_lng = req.lng if req.lng is not None else DELHI["lng"]
    region = (req.region or DEFAULT_REGION).upper()
    language = req.language or DEFAULT_LANGUAGE

    # Simple sample data generation biased towards Delhi coordinates.
    base_samples: List[Restaurant] = [
        Restaurant(place_id="sample_1", name="Connaught Place Bistro", lat=center_lat + 0.005, lng=center_lng + 0.005, rating=4.2, vicinity="Connaught Place, New Delhi"),
        Restaurant(place_id="sample_2", name="Karol Bagh Eats", lat=center_lat - 0.003, lng=center_lng + 0.004, rating=4.0, vicinity="Karol Bagh, New Delhi"),
        Restaurant(place_id="sample_3", name="Old Delhi Tandoor", lat=center_lat + 0.002, lng=center_lng - 0.006, rating=4.5, vicinity="Chandni Chowk, Old Delhi"),
        Restaurant(place_id="sample_4", name="South Delhi Cafe", lat=center_lat - 0.004, lng=center_lng - 0.003, rating=4.1, vicinity="Hauz Khas, South Delhi"),
    ]

    keyword = (req.keyword or "").strip().lower()
    if keyword:
        filtered = [r for r in base_samples if keyword in r.name.lower() or keyword in (r.vicinity or "").lower()]
    else:
        filtered = base_samples

    response = NearbySearchResponse(
        results=filtered,
        center={"lat": center_lat, "lng": center_lng},
        region=region,
        language=language,
    )
    return response

# PUBLIC_INTERFACE
@app.get(
    "/api/restaurants/{place_id}",
    tags=["restaurants"],
    summary="Restaurant details",
    description="Returns sample details for a restaurant. This demo endpoint does not require external APIs.",
)
def place_details(place_id: str) -> Dict[str, Any]:
    """Return stubbed place details suitable for demo without external API keys."""
    sample = {
        "place_id": place_id,
        "name": "Sample Restaurant",
        "formatted_address": "New Delhi, Delhi 110001, India",
        "international_phone_number": "+91 11 1234 5678",
        "rating": 4.2,
        "user_ratings_total": 128,
        "website": "https://example.com",
        "url": "https://maps.google.com/?q=Delhi",
    }
    return sample
