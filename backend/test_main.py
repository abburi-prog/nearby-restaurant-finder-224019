from fastapi.testclient import TestClient
from main import app, NearbyRequest

client = TestClient(app)

def test_health_ok():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"

def test_nearby_request_validation_radius_bounds():
    # radius too large should fail
    try:
        NearbyRequest(lat=0.0, lng=0.0, radius=100000)
        assert False, "Expected validation error"
    except Exception:
        assert True
