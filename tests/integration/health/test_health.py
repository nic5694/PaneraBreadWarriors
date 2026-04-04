import pytest


@pytest.mark.integration
def test_health_endpoint_returns_200_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
