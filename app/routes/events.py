from flask import Blueprint, jsonify, request

from app.services import EventService, UrlNotFoundError, EventCreateError

events_bp = Blueprint("events", __name__, url_prefix="/events/v1/api/events")


event_service = EventService()


@events_bp.get("/")
def list_events():
    return jsonify({"data": event_service.list_events()}), 200


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

    try:
        event = event_service.create_event(data)
    except ValueError as exc:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc)
            }
        }), 400
    except UrlNotFoundError as exc:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": str(exc)
            }
        }), 404
    except EventCreateError as exc:
        return jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to create event",
                "details": str(exc),
            }
        }), 500

    return jsonify({"data": event}), 201