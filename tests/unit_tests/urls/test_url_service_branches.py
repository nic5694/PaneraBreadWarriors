from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from peewee import IntegrityError

from app.services.url_service import UrlConflictError, UrlService, _extract_constraint_name


def _mock_url_row():
    row = MagicMock()
    row.id = 1
    row.user_id = "1"
    row.shortcode = "abc123"
    row.original_url = "https://example.com/a"
    row.title = "Example"
    row.is_active = True
    row.created_at = datetime(2026, 1, 1)
    row.updated_at = datetime(2026, 1, 1)
    return row


def test_extract_constraint_name_returns_none_without_wrapped_exception():
    assert _extract_constraint_name(Exception("plain")) is None


def test_create_url_generates_shortcode_when_missing(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.secrets.choice", return_value="A"):
        with patch("app.services.url_service.Url.create", return_value=_mock_url_row()) as mock_create:
            service = UrlService()
            service.create_url({"user_id": "1", "original_url": "https://example.com/a"})

    created_shortcode = mock_create.call_args.kwargs["shortcode"]
    assert created_shortcode == "AAAAAA"


def test_create_url_recovers_from_pkey_drift(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    first = IntegrityError("urls_pkey")
    mock_db = MagicMock()
    with patch("app.services.url_service.Url.create", side_effect=[first, _mock_url_row()]) as mock_create:
        with patch("app.services.url_service.Url._meta.database", new=mock_db):
            service = UrlService()
            result = service.create_url(
                {"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"}
            )

    assert result["shortcode"] == "abc123"
    assert mock_create.call_count == 2
    assert mock_db.execute_sql.call_count == 1


def test_create_url_pkey_retry_still_conflict_raises_shortcode_error(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    mock_db = MagicMock()
    with patch(
        "app.services.url_service.Url.create",
        side_effect=[IntegrityError("urls_pkey"), IntegrityError("duplicate")],
    ):
        with patch("app.services.url_service.Url._meta.database", new=mock_db):
            service = UrlService()
            with pytest.raises(UrlConflictError, match="shortcode already exists"):
                service.create_url(
                    {"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"}
                )


def test_create_url_shortcode_conflict_raises_conflict_error(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.create", side_effect=IntegrityError("shortcode conflict")):
        service = UrlService()
        with pytest.raises(UrlConflictError, match="shortcode already exists"):
            service.create_url(
                {"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"}
            )


def test_create_url_unknown_integrity_error_raises_generic_conflict(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.create", side_effect=IntegrityError("something else")):
        service = UrlService()
        with pytest.raises(UrlConflictError, match="database integrity conflict"):
            service.create_url(
                {"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"}
            )


def test_list_urls_returns_cache_hit_without_query(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.return_value = [{"id": 1}]
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.select") as mock_select:
        service = UrlService()
        result = service.list_urls(user_id="1", is_active="true")

    assert result == [{"id": 1}]
    mock_select.assert_not_called()


def test_list_urls_returns_empty_when_select_raises(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.return_value = None
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.select", side_effect=RuntimeError("db down")):
        service = UrlService()
        assert service.list_urls() == []


def test_get_url_by_id_returns_none_when_not_found(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.return_value = None
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.get_or_none", return_value=None):
        service = UrlService()
        assert service.get_url_by_id(123) is None


def test_get_url_by_id_returns_cache_hit(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.return_value = {"id": 7}
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.get_or_none") as mock_get:
        service = UrlService()
        result = service.get_url_by_id(7)

    assert result == {"id": 7}
    mock_get.assert_not_called()


def test_update_url_returns_none_when_not_found(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.get_or_none", return_value=None):
        service = UrlService()
        assert service.update_url(11, {"title": "new"}) is None


def test_delete_url_returns_false_when_not_found(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    with patch("app.services.url_service.Url.get_or_none", return_value=None):
        service = UrlService()
        assert service.delete_url(11) is False


def test_create_url_uses_constraint_name_for_shortcode_conflict(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.url_service.cache", fake_cache)

    diag = SimpleNamespace(constraint_name="urls_shortcode_key")
    orig = SimpleNamespace(diag=diag)
    error = IntegrityError("duplicate")
    error.orig = orig

    with patch("app.services.url_service.Url.create", side_effect=error):
        service = UrlService()
        with pytest.raises(UrlConflictError, match="shortcode already exists"):
            service.create_url(
                {"user_id": "1", "original_url": "https://example.com/a", "shortcode": "abc123"}
            )