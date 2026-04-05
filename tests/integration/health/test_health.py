import pytest


@pytest.mark.integration
def test_health_endpoint_returns_200_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


@pytest.mark.integration
def test_ready_endpoint_returns_200_when_db_is_available(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}
