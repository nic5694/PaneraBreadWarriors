import json

import pytest

from app.database import db


def _create_url(client, shortcode="event-code", original_url="https://example.com/event"):
    response = client.post(
        "/urls/v1/api/urls/",
        json={
            "user_id": "1",
            "shortcode": shortcode,
            "original_url": original_url,
        },
    )
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

    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": "click"},
    )
    client.post(
        "/events/v1/api/events/",
        json={"url_id": url_id, "event_type": "view"},
    )

    response = client.get("/events/v1/api/events/")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 2
    assert [event["event_type"] for event in data] == ["click", "view"]


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
