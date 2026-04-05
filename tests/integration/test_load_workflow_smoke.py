import uuid

import pytest


@pytest.mark.integration
def test_load_workflow_endpoints_smoke(client):
    unique = uuid.uuid4().hex[:8]

    create_user_response = client.post(
        "/users",
        json={
            "name": f"load-user-{unique}",
            "email": f"load-user-{unique}@example.com",
            "password": "password123",
        },
    )
    assert create_user_response.status_code == 201
    user_id = create_user_response.get_json()["data"]["id"]

    create_url_response = client.post(
        "/urls/",
        json={
            "user_id": str(user_id),
            "shortcode": f"lt-{uuid.uuid4().hex[:12]}",
            "original_url": f"https://example.com/{unique}",
            "title": "Load test URL",
        },
    )
    assert create_url_response.status_code == 201
    url_data = create_url_response.get_json()["data"]

    create_event_response = client.post(
        "/events",
        json={"url_id": url_data["id"], "event_type": "click"},
    )
    assert create_event_response.status_code == 201

    health_response = client.get("/health")
    assert health_response.status_code == 200

    list_users_response = client.get("/users")
    assert list_users_response.status_code == 200

    get_user_response = client.get(f"/users/{user_id}")
    assert get_user_response.status_code == 200

    update_user_response = client.patch(
        f"/users/{user_id}",
        json={
            "name": f"load-user-{unique}-updated",
            "email": f"load-user-{unique}-updated@example.com",
        },
    )
    assert update_user_response.status_code == 200

    resolve_shortcode_response = client.get(
        f"/r/{url_data['shortcode']}", follow_redirects=False
    )
    assert resolve_shortcode_response.status_code == 302
    assert resolve_shortcode_response.headers["Location"] == url_data["original_url"]

    list_events_response = client.get("/events")
    assert list_events_response.status_code == 200
    events = list_events_response.get_json()["data"]
    assert any(
        event["event_type"] == "click" and event["url_id"] == str(url_data["id"])
        for event in events
    )

    delete_user_response = client.delete(f"/users/{user_id}")
    assert delete_user_response.status_code == 200
