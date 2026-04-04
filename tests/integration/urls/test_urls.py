import pytest

from app.database import db


@pytest.mark.integration
def test_create_url_returns_201_and_payload(client):
    payload = {
        "user_id": "1",
        "shortcode": "abc123",
        "original_url": "https://example.com/a",
        "title": "Example",
    }

    response = client.post("/urls/v1/api/urls/", json=payload)

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["id"] == 1
    assert data["shortcode"] == payload["shortcode"]
    assert data["original_url"] == payload["original_url"]


@pytest.mark.integration
def test_create_url_duplicate_shortcode_returns_409(client):
    payload = {
        "user_id": "1",
        "shortcode": "dup-code",
        "original_url": "https://example.com/a",
    }
    client.post("/urls/v1/api/urls/", json=payload)

    response = client.post("/urls/v1/api/urls/", json=payload)

    assert response.status_code == 409
    assert response.get_json()["error"] == {
        "code": "CONFLICT",
        "message": "shortcode already exists",
    }


@pytest.mark.integration
def test_create_url_sequence_drift_returns_409_with_specific_message(client):
    client.post(
        "/urls/v1/api/urls/",
        json={"user_id": "1", "shortcode": "code-1", "original_url": "https://example.com/1"},
    )
    client.post(
        "/urls/v1/api/urls/",
        json={"user_id": "1", "shortcode": "code-2", "original_url": "https://example.com/2"},
    )

    with client.application.app_context():
        with db.connection_context():
            db.execute_sql(
                "SELECT setval(pg_get_serial_sequence('urls', 'id'), 1, true);"
            )

    response = client.post(
        "/urls/v1/api/urls/",
        json={"user_id": "1", "shortcode": "code-3", "original_url": "https://example.com/3"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == {
        "code": "CONFLICT",
        "message": "url id sequence is out of sync",
    }


@pytest.mark.integration
def test_create_url_missing_fields_returns_400(client):
    response = client.post(
        "/urls/v1/api/urls/",
        json={"user_id": "1", "shortcode": "abc123"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "BAD_REQUEST",
        "message": "user_id, shortcode, and original_url are required",
    }


@pytest.mark.integration
def test_resolve_shortcode_redirects_returns_302(client):
    client.post(
        "/urls/v1/api/urls/",
        json={"user_id": "1", "shortcode": "go", "original_url": "https://example.com/go"},
    )

    response = client.get("/r/go", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/go"


@pytest.mark.integration
def test_resolve_shortcode_returns_404_not_found(client):
    response = client.get("/r/missing", follow_redirects=False)

    assert response.status_code == 404
    assert response.get_json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Short URL not found",
    }
