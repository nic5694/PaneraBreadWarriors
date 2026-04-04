import json
import uuid  
import pytest
from app.database import db

# Modified helper to ensure unique shortcodes for every test run
def _create_url(client, shortcode=None, original_url=None):
    # 1. Create a fresh user first to avoid User-related conflicts
    user_email = f"test-{uuid.uuid4().hex[:6]}@gatech.edu"
    user_res = client.post("/users/v1/api/users/", json={
        "name": "Test User",
        "email": user_email,
        "password": "testpassword123"
    })
    # If this fails with 409, it's fine, but we need a valid user_id
    user_id = user_res.get_json()["data"]["id"] if user_res.status_code == 201 else 1

    if shortcode is None:
        shortcode = f"test-{uuid.uuid4().hex[:8]}"
    if original_url is None:
        original_url = f"https://example.com/{uuid.uuid4().hex[:6]}"

    response = client.post(
        "/urls/v1/api/urls/",
        json={
            "user_id": str(user_id), # Use the fresh user
            "shortcode": shortcode,
            "original_url": original_url, # Make this unique too
        },
    )
    
    # If it's STILL 409, we need to see the error message
    if response.status_code != 201:
        print(f"DEBUG: Response Body: {response.get_json()}")
        
    assert response.status_code == 201
    return response.get_json()["data"]["id"]

@pytest.mark.integration
def test_create_event_returns_201_and_payload(client):
    url_id = _create_url(client)

    response = client.post(
        "/events/v1/api/events/",
        json={
            "url_id": url_id,
            "event_type": "click",
            "details": {"ip": "127.0.0.1"},
        },
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["url_id"] == str(url_id)
    assert data["event_type"] == "click"
    assert json.loads(data["details"]) == {"ip": "127.0.0.1"}


@pytest.mark.integration
def test_create_event_missing_required_fields_returns_400(client):
    response = client.post(
        "/events/v1/api/events/",
        json={"url_id": 1},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "BAD_REQUEST",
        "message": "url_id and event_type are required",
    }


@pytest.mark.integration
def test_create_event_returns_404_when_url_does_not_exist(client):
    response = client.post(
        "/events/v1/api/events/",
        json={"url_id": 9999, "event_type": "click"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == {
        "code": "NOT_FOUND",
        "message": "URL with id 9999 not found",
    }


@pytest.mark.integration
def test_list_events_returns_created_events(client):
    url_id = _create_url(client)
    
    # Generate unique event types to find them easily in a large database
    type_1 = f"click-{uuid.uuid4().hex[:4]}"
    type_2 = f"view-{uuid.uuid4().hex[:4]}"

    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": type_1},
    )
    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": type_2},
    )

    response = client.get("/events/v1/api/events/")

    assert response.status_code == 200
    data = response.get_json()["data"]
    
    # Instead of checking total length (which is 3400+), 
    # we verify our specific new events exist in the response.
    event_types = [event["event_type"] for event in data]
    assert type_1 in event_types
    assert type_2 in event_types


@pytest.mark.integration
def test_create_event_recovers_from_sequence_drift(client):
    url_id = _create_url(client)

    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": "click"},
    )
    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": "view"},
    )

    with client.application.app_context():
        with db.connection_context():
            db.execute_sql(
                "SELECT setval(pg_get_serial_sequence('events', 'id'), 1, true);"
            )

    response = client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": "redirect"},
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["event_type"] == "redirect"