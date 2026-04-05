from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.url_service import UrlService


def test_resolve_shortcode_uses_cache_after_initial_lookup(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.side_effect = [None, "https://example.com/a"]
    fake_cache.set_json.return_value = True
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    url = MagicMock()
    url.id = 1
    url.user_id = "1"
    url.shortcode = "abc123"
    url.original_url = "https://example.com/a"
    url.title = "Example"
    url.is_active = True
    url.created_at = datetime(2026, 1, 1)
    url.updated_at = datetime(2026, 1, 1)

    with patch("app.services.url_service.Url.get_or_none", return_value=url) as mock_get:
        service = UrlService()

        first = service.resolve_shortcode("abc123")
        second = service.resolve_shortcode("abc123")

    assert first == "https://example.com/a"
    assert second == "https://example.com/a"
    assert mock_get.call_count == 1
    assert fake_cache.set_json.call_count == 1


def test_create_url_invalidates_url_cache(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    url = MagicMock()
    url.id = 1
    url.user_id = "1"
    url.shortcode = "abc123"
    url.original_url = "https://example.com/a"
    url.title = "Example"
    url.is_active = True
    url.created_at = datetime(2026, 1, 1)
    url.updated_at = datetime(2026, 1, 1)

    with patch("app.services.url_service.Url.create", return_value=url):
        service = UrlService()
        service.create_url({"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"})

    fake_cache.invalidate_namespace.assert_called_once_with("urls")