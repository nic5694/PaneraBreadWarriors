import pytest
from unittest.mock import MagicMock, patch
from app.services import UrlService, UrlConflictError

# ---------------------------------------------------------
# Service Layer Unit Tests
# ---------------------------------------------------------

@patch("app.models.urls.Url.create")
def test_create_url_service_success(mock_url_create):
    """Test that the service correctly interacts with the Url model to create a record."""
    service = UrlService()

    mock_url_instance = MagicMock()
    mock_url_instance.id = 1
    mock_url_instance.shortcode = "gt-omscs"
    mock_url_instance.original_url = "https://omscs.gatech.edu"

    mock_url_create.return_value = mock_url_instance

    data = {
        "user_id": "401",
        "shortcode": "gt-omscs",
        "original_url": "https://omscs.gatech.edu"
    }

    result = service.create_url(data)

    assert result["id"] == 1
    assert result["shortcode"] == "gt-omscs"
    mock_url_create.assert_called_once()


def test_create_url_service_validation():
    """Test that the service raises ValueError if required fields are missing."""
    service = UrlService()

    with pytest.raises(ValueError) as exc:
        service.create_url({
            "user_id": "401",
            "shortcode": "test"
        })

    assert "original_url" in str(exc.value)


@patch("app.models.urls.Url.create")
def test_create_url_service_conflict(mock_url_create):
    """Test that the service raises UrlConflictError when shortcode already exists."""
    service = UrlService()

    mock_url_create.side_effect = UrlConflictError("shortcode already exists")

    data = {
        "user_id": "401",
        "shortcode": "gt-omscs",
        "original_url": "https://omscs.gatech.edu"
    }

    with pytest.raises(UrlConflictError) as exc:
        service.create_url(data)

    assert "shortcode already exists" in str(exc.value)


@patch("app.models.urls.Url.get_or_none")
def test_resolve_shortcode_service(mock_get):
    """Test that the service correctly fetches the original URL for a shortcode."""
    service = UrlService()

    mock_get.return_value = MagicMock(original_url="https://google.com")

    url = service.resolve_shortcode("goog")

    assert url == "https://google.com"


# ---------------------------------------------------------
# Route (Blueprint) Unit Tests
# ---------------------------------------------------------

def test_create_url_route_success(client):
    """Test the POST route successful creation."""
    with patch("app.routes.urls.url_service.create_url") as mocked_service:
        mocked_service.return_value = {"id": 1, "shortcode": "test"}

        # Using the path that worked in your last run
        response = client.post("/urls/", json={
            "user_id": "1",
            "shortcode": "test",
            "original_url": "https://test.com"
        })

        assert response.status_code == 201
        assert response.get_json()["data"]["shortcode"] == "test"


def test_resolve_shortcode_route_redirect(client):
    """Test that the redirect route works correctly for a valid shortcode."""
    with patch("app.routes.urls.url_service.resolve_shortcode") as mocked_resolve:
        mocked_resolve.return_value = "https://gatech.edu"

        # Using the path that worked in your last run
        response = client.get("/urls/gt")

        assert response.status_code == 302
        assert response.location == "https://gatech.edu"


def test_resolve_shortcode_route_404(client):
    """Test that an invalid shortcode returns a 404 error."""
    with patch("app.routes.urls.url_service.resolve_shortcode") as mocked_resolve:
        mocked_resolve.return_value = None

        # Matches the successful /urls/gt pattern
        response = client.get("/urls/invalid")

        assert response.status_code == 404
        
        # Verify JSON response
        json_data = response.get_json()
        assert json_data is not None, "Response was not JSON (Check your error handler)"
        assert json_data["error"]["code"] == "NOT_FOUND"