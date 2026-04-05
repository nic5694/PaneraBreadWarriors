from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.event_service import EventService


def test_list_events_uses_cache_after_initial_lookup(monkeypatch):
    fake_cache = MagicMock()
    fake_cache.get_json.side_effect = [None, [{"id": 1, "event_type": "click"}]]
    fake_cache.set_json.return_value = True
    monkeypatch.setattr("app.services.event_service.cache", fake_cache)

    event = MagicMock()
    event.id = 1
    event.url_id = "1"
    event.user_id = "2"
    event.event_type = "click"
    event.timestamp = datetime(2026, 1, 1)
    event.details = None
    event.created_at = datetime(2026, 1, 1)
    event.updated_at = datetime(2026, 1, 1)

    query = MagicMock()
    query.order_by.return_value = [event]

    with patch("app.services.event_service.Event.select", return_value=query) as mock_select:
        service = EventService()

        first = service.list_events()
        second = service.list_events()

    assert first[0]["event_type"] == "click"
    assert second == [{"id": 1, "event_type": "click"}]
    assert mock_select.call_count == 1
    assert fake_cache.set_json.call_count == 1


def test_create_event_invalidates_event_cache(monkeypatch):
    fake_cache = MagicMock()
    monkeypatch.setattr("app.services.event_service.cache", fake_cache)

    event = MagicMock()
    event.id = 1
    event.url_id = "1"
    event.user_id = "2"
    event.event_type = "click"
    event.timestamp = datetime(2026, 1, 1)
    event.details = None
    event.created_at = datetime(2026, 1, 1)
    event.updated_at = datetime(2026, 1, 1)

    with patch("app.services.event_service.Url.get_by_id", return_value=MagicMock(id=1)):
        with patch("app.services.event_service.Event.create", return_value=event):
            service = EventService()
            service.create_event({"url_id": "1", "event_type": "click"})

    fake_cache.invalidate_namespace.assert_called_once_with("events")