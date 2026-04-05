from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.user_service import UserService


def test_get_user_uses_cache_after_initial_lookup(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.side_effect = [
        None,
        {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "is_active": True,
        },
    ]
    fake_cache.set_json.return_value = True
    monkeypatch.setattr("app.services.user_service.cache", fake_cache)

    user = MagicMock()
    user.id = 1
    user.name = "Alice"
    user.email = "alice@example.com"
    user.created_at = datetime(2026, 1, 1)
    user.updated_at = datetime(2026, 1, 1)
    user.is_active = True

    with patch("app.services.user_service.User.get_or_none", return_value=user) as mock_get:
        service = UserService()

        first = service.get_user(1)
        second = service.get_user(1)

    assert first["email"] == "alice@example.com"
    assert second["email"] == "alice@example.com"
    assert mock_get.call_count == 1
    assert fake_cache.set_json.call_count == 1


def test_create_user_invalidates_user_cache(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.user_service.cache", fake_cache)

    user = MagicMock()
    user.id = 1
    user.name = "Alice"
    user.email = "alice@example.com"
    user.created_at = datetime(2026, 1, 1)
    user.updated_at = datetime(2026, 1, 1)
    user.is_active = True

    with patch("app.services.user_service.User.create", return_value=user):
        service = UserService()
        service.create_user({"name": "Alice", "email": "alice@example.com", "password": "secret"})

    fake_cache.invalidate_namespace.assert_called_once_with("users")