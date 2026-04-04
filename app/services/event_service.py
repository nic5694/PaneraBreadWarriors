import json
import logging

from peewee import IntegrityError

from app.models.events import Event
from app.models.urls import Url


logger = logging.getLogger(__name__)


class UrlNotFoundError(Exception):
    pass


class EventCreateError(Exception):
    pass


class EventService:
    def serialize_event(self, event):
        return {
            "id": event.id,
            "url_id": event.url_id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
        }

    def list_events(self):
        events = Event.select().order_by(Event.id)
        return [self.serialize_event(event) for event in events]

    def create_event(self, data):
        url_id = data.get("url_id")
        event_type = data.get("event_type")

        if not url_id or not event_type:
            raise ValueError("url_id and event_type are required")

        # Validate that the URL exists.
        try:
            Url.get_by_id(url_id)
        except Url.DoesNotExist as exc:
            raise UrlNotFoundError(f"URL with id {url_id} not found") from exc
        except Exception as exc:
            logger.warning(
                "Error validating URL for event. url_id=%s error=%s",
                url_id,
                exc,
            )

        details = data.get("details")
        if isinstance(details, (dict, list)):
            details = json.dumps(details)

        create_payload = {
            "url_id": str(url_id),
            "user_id": str(data.get("user_id")) if data.get("user_id") is not None else None,
            "event_type": event_type,
            "details": details,
        }

        try:
            event = Event.create(**create_payload)
        except IntegrityError as exc:
            if "events_pkey" in str(exc):
                logger.warning(
                    "Detected events id sequence drift. Resyncing sequence. error=%s",
                    exc,
                )
                Event._meta.database.execute_sql(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('events', 'id'),
                        COALESCE((SELECT MAX(id) FROM events), 1),
                        true
                    )
                    """
                )
                event = Event.create(**create_payload)
            else:
                raise
        except Exception as exc:
            logger.exception(
                "Failed to create event. payload=%s error=%s",
                data,
                exc,
            )
            raise EventCreateError(str(exc)) from exc

        return self.serialize_event(event)
