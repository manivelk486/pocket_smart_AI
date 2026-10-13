from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home_page():
    response = client.get("/")

    assert response.status_code == 200
    assert "PocketSmart" in response.text


def test_api_information():
    response = client.get("/api")

    assert response.status_code == 200
    assert response.json()["application"] == "PocketSmart AI"


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_docs_available():
    response = client.get("/docs")

    assert response.status_code == 200


def test_planner_requires_login():
    response = client.post(
        "/api/planners",
        json={
            "plan_type": "home",
            "budget": 10000,
            "currency": "INR",
        },
    )

    assert response.status_code == 401