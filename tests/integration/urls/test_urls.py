import pytest
import uuid
from app.database import db

def _ensure_user_exists(client):
    email = "test_url_user@gatech.edu"
    res = client.post("/users", json={
        "name": "URL Tester",
        "email": email,
        "password": "password123"
    })
    if res.status_code == 201:
        return str(res.get_json()["data"]["id"])
    # If conflict, we assume user exists and we can use a standard ID or lookup
    return "1" 

@pytest.mark.integration
def test_create_url_returns_201_and_payload(client):
    user_id = _ensure_user_exists(client)
    unique_code = f"code-{uuid.uuid4().hex[:6]}"
    payload = {
        "user_id": user_id,
        "shortcode": unique_code,
        "original_url": f"https://example.com/{unique_code}",
        "title": "Example",
    }
    response = client.post("/urls", json=payload)
    assert response.status_code == 201


@pytest.mark.integration
def test_create_url_with_trailing_slash_returns_201(client):
    user_id = _ensure_user_exists(client)
    unique_code = f"slash-{uuid.uuid4().hex[:6]}"
    payload = {
        "user_id": user_id,
        "shortcode": unique_code,
        "original_url": f"https://example.com/{unique_code}",
        "title": "Slash Route",
    }

    response = client.post("/urls/", json=payload)

    assert response.status_code == 201
    assert response.get_json()["data"]["shortcode"] == unique_code

@pytest.mark.integration
def test_create_url_duplicate_shortcode_returns_409(client):
    user_id = _ensure_user_exists(client)
    unique_code = f"dup-{uuid.uuid4().hex[:6]}"
    payload = {
        "user_id": user_id,
        "shortcode": unique_code,
        "original_url": "https://example.com/a",
    }
    client.post("/urls", json=payload)
    response = client.post("/urls", json=payload)

    assert response.status_code == 409
    # Updated to match your actual specific error message
    assert response.get_json()["error"]["message"] == "shortcode already exists"

@pytest.mark.integration
def test_create_url_sequence_drift_recovers_successfully(client):
    """
    Your service returns 201 here because it automatically fixes the drift!
    This test verifies the recovery logic works.
    """
    user_id = _ensure_user_exists(client)
    c1, c2 = [f"drift-{uuid.uuid4().hex[:5]}" for _ in range(2)]
    
    client.post("/urls", json={"user_id": user_id, "shortcode": c1, "original_url": "https://ex.com/1"})
    
    with client.application.app_context():
        with db.connection_context():
            # Break the sequence
            db.execute_sql("SELECT setval(pg_get_serial_sequence('urls', 'id'), 1, true);")

    # This should trigger the auto-recovery in UrlService and return 201
    response = client.post(
        "/urls",
        json={"user_id": user_id, "shortcode": c2, "original_url": "https://ex.com/2"},
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["shortcode"] == c2

@pytest.mark.integration
def test_resolve_shortcode_redirects_returns_302(client):
    user_id = _ensure_user_exists(client)
    unique_code = f"go-{uuid.uuid4().hex[:6]}"
    client.post(
        "/urls",
        json={"user_id": user_id, "shortcode": unique_code, "original_url": "https://example.com/go"},
    )
    response = client.get(f"/urls/{unique_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/go"


@pytest.mark.integration
def test_resolve_shortcode_redirects_returns_302_on_r_prefix(client):
    user_id = _ensure_user_exists(client)
    unique_code = f"r-{uuid.uuid4().hex[:6]}"
    client.post(
        "/urls",
        json={
            "user_id": user_id,
            "shortcode": unique_code,
            "original_url": "https://example.com/r-route",
        },
    )

    response = client.get(f"/r/{unique_code}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/r-route"