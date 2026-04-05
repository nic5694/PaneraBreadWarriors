import pytest

from app.database import db


@pytest.mark.integration
def test_create_user_returns_201_and_payload(client):
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "password123",
    }

    response = client.post("/users", json=payload)

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["id"] == 1
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["is_active"] is True


@pytest.mark.integration
def test_create_user_duplicate_email_returns_409(client):
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "password123",
    }
    client.post("/users", json=payload)

    response = client.post("/users", json=payload)

    assert response.status_code == 409
    assert response.get_json()["error"] == {
        "code": "CONFLICT",
        "message": "email already exists",
    }


@pytest.mark.integration
def test_create_user_sequence_drift_returns_409_with_specific_message(client):
    client.post(
            "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    client.post(
        "/users",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )

    with client.application.app_context():
        with db.connection_context():
            db.execute_sql(
                "SELECT setval(pg_get_serial_sequence('users', 'id'), 1, true);"
            )

    response = client.post(
        "/users",
        json={"name": "Charlie", "email": "charlie@example.com", "password": "password123"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == {
        "code": "CONFLICT",
        "message": "user id sequence is out of sync",
    }


@pytest.mark.integration
def test_create_user_missing_password_is_accepted_on_legacy_users_path(client):
    response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["email"] == "alice@example.com"


@pytest.mark.integration
def test_list_users_returns_created_users(client):
    client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    client.post(
        "/users",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )

    response = client.get("/users")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["kind"] == "list"
    assert data["total_items"] == 2
    assert [user["email"] for user in data["sample"]] == ["alice@example.com", "bob@example.com"]


@pytest.mark.integration
def test_get_user_returns_200_for_existing_user(client):
    create_response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    user_id = create_response.get_json()["data"]["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "alice@example.com"


@pytest.mark.integration
def test_get_user_returns_404_for_missing_user(client):
    response = client.get("/users/9999")

    assert response.status_code == 404
    assert response.get_json()["error"] == {
        "code": "NOT_FOUND",
        "message": "User not found",
    }


@pytest.mark.integration
def test_update_user_updates_name_and_email(client):
    create_response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    user_id = create_response.get_json()["data"]["id"]

    response = client.patch(
        f"/users/{user_id}",
        json={"name": "Alice Updated", "email": "alice.updated@example.com"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["name"] == "Alice Updated"
    assert data["email"] == "alice.updated@example.com"


@pytest.mark.integration
def test_update_user_with_duplicate_email_returns_409(client):
    user1 = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    ).get_json()["data"]
    client.post(
        "/users",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"},
    )

    response = client.patch(
        f"/users/{user1['id']}",
        json={"email": "bob@example.com"},
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == {
        "code": "CONFLICT",
        "message": "email already exists",
    }


@pytest.mark.integration
def test_delete_user_soft_deletes_and_followup_get_returns_404(client):
    create_response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    user_id = create_response.get_json()["data"]["id"]

    delete_response = client.delete(f"/users/{user_id}")
    get_response = client.get(f"/users/{user_id}")

    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == "User deleted successfully"
    assert get_response.status_code == 404
    assert get_response.get_json()["error"]["message"] == "User not found"
