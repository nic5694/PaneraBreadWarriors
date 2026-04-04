import json

from flask import Blueprint, current_app, jsonify, request
from peewee import IntegrityError

from app.models.events import Event
from app.models.urls import Url

events_bp = Blueprint("events", __name__, url_prefix="/events/v1/api/events")


def serialize_event(event):
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


@events_bp.get("/")
def list_events():
    events = Event.select().order_by(Event.id)
    return jsonify({
        "data": [serialize_event(event) for event in events]
    }), 200


@events_bp.post("/")
def create_event():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Request body must be valid JSON"
            }
        }), 400

    url_id = data.get("url_id")
    event_type = data.get("event_type")

    if not url_id or not event_type:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "url_id and event_type are required"
            }
        }), 400

    # Validate that the URL exists
    try:
        Url.get_by_id(url_id)
    except Url.DoesNotExist:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"URL with id {url_id} not found"
            }
        }), 404
    except Exception as exc:
        current_app.logger.warning(
            "Error validating URL for event. url_id=%s error=%s",
            url_id,
            exc,
        )
        # Don't fail the event creation if URL validation fails due to DB issues
        pass

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
        # If seed/import inserted explicit IDs, the sequence can lag behind max(id).
        # Resync and retry once so event writes recover automatically.
        if "events_pkey" in str(exc):
            current_app.logger.warning(
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
        current_app.logger.exception(
            "Failed to create event. payload=%s error=%s",
            data,
            exc,
        )
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to create event",
                "details": str(exc),
            }
        }), 500

    return jsonify({"data": serialize_event(event)}), 201