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
        # Attempt to parse 'details' back into a dict/list if it's a JSON string
        # This ensures the API returns actual JSON objects instead of escaped strings
        details = event.details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except (ValueError, TypeError):
                pass

        return {
            "id": event.id,
            "url_id": event.url_id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else event.timestamp,
            "details": details,
            "created_at": event.created_at.isoformat() if hasattr(event.created_at, 'isoformat') else event.created_at,
            "updated_at": event.updated_at.isoformat() if hasattr(event.updated_at, 'isoformat') else event.updated_at,
        }

    def list_events(self, filters=None):
        """
        Retrieves events with optional filtering.
        :param filters: dict containing url_id, user_id, or event_type
        """
        query = Event.select()

        if filters:
            if filters.get("url_id"):
                query = query.where(Event.url_id == str(filters["url_id"]))
            if filters.get("user_id"):
                query = query.where(Event.user_id == str(filters["user_id"]))
            if filters.get("event_type"):
                query = query.where(Event.event_type == filters["event_type"])

        events = query.order_by(Event.id)
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
            # Handle Postgres sequence drift
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