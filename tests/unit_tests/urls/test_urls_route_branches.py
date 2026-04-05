from unittest.mock import patch


def test_create_url_returns_400_on_validation_error(client):
    with patch("app.routes.urls.url_service.create_url", side_effect=ValueError("bad payload")):
        response = client.post("/urls", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "BAD_REQUEST",
        "message": "bad payload",
    }


def test_list_urls_reads_user_id_from_json_body(client):
    with patch("app.routes.urls.url_service.list_urls", return_value=[]) as mock_list:
        response = client.get("/urls", json={"user_id": "42"})

    assert response.status_code == 200
    mock_list.assert_called_once_with(user_id="42", is_active=None)


def test_list_urls_returns_500_when_service_raises(client):
    with patch("app.routes.urls.url_service.list_urls", side_effect=RuntimeError("boom")):
        response = client.get("/urls")

    assert response.status_code == 500
    assert response.get_json()["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "Failed to retrieve URLs",
    }


def test_get_url_by_id_returns_404_when_missing(client):
    with patch("app.routes.urls.url_service.get_url_by_id", return_value=None):
        response = client.get("/urls/999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_put_url_returns_404_when_missing(client):
    with patch("app.routes.urls.url_service.update_url", return_value=None):
        response = client.put("/urls/10", json={"title": "new"})

    assert response.status_code == 404
    assert response.get_json()["error"]["message"] == "URL not found"


def test_put_url_returns_200_when_updated(client):
    payload = {"id": 10, "shortcode": "abc123", "original_url": "https://example.com"}
    with patch("app.routes.urls.url_service.update_url", return_value=payload):
        response = client.put("/urls/10", json={"title": "updated"})

    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == 10


def test_delete_url_returns_204(client):
    with patch("app.routes.urls.url_service.delete_url", return_value=True) as mock_delete:
        response = client.delete("/urls/12")

    assert response.status_code == 204
    mock_delete.assert_called_once_with(12)


def test_resolve_shortcode_returns_404_when_missing(client):
    with patch("app.routes.urls.url_service.resolve_shortcode", return_value=None):
        response = client.get("/urls/missing-code")

    assert response.status_code == 404
    assert response.get_json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Shortcode not found",
    }