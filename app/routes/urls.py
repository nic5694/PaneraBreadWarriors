from flask import Blueprint, jsonify, request, redirect
from peewee import IntegrityError

from app.models.urls import Url

urls_bp = Blueprint("urls", __name__)


def _extract_constraint_name(exc):
    wrapped_exc = getattr(exc, "__cause__", None) or getattr(exc, "orig", None)
    if wrapped_exc is not None:
        diag = getattr(wrapped_exc, "diag", None)
        if diag is not None:
            return getattr(diag, "constraint_name", None)
    return None


def _classify_url_integrity_error(exc):
    constraint_name = _extract_constraint_name(exc)
    error_text = str(exc).lower()

    if constraint_name and "shortcode" in constraint_name:
        return "shortcode already exists"

    if constraint_name and "urls_pkey" in constraint_name:
        return "url id sequence is out of sync"

    if "shortcode" in error_text and "duplicate" in error_text:
        return "shortcode already exists"

    if "urls_pkey" in error_text or "duplicate key value" in error_text:
        return "url id sequence is out of sync"

    return "database integrity conflict"


def serialize_url(url):
    return {
        "id": url.id,
        "user_id": url.user_id,
        "shortcode": url.shortcode,
        "original_url": url.original_url,
        "title": url.title,
        "is_active": url.is_active,
        "created_at": url.created_at.isoformat(),
        "updated_at": url.updated_at.isoformat(),
    }


@urls_bp.post("/urls/v1/api/urls/")
def create_url():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Request body must be valid JSON"
            }
        }), 400

    user_id = data.get("user_id")
    shortcode = data.get("shortcode")
    original_url = data.get("original_url")

    if not user_id or not shortcode or not original_url:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "user_id, shortcode, and original_url are required"
            }
        }), 400

    try:
        url = Url.create(
            user_id=user_id,
            shortcode=shortcode,
            original_url=original_url,
            title=data.get("title"),
        )
    except IntegrityError as exc:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": _classify_url_integrity_error(exc)
            }
        }), 409

    return jsonify({"data": serialize_url(url)}), 201


@urls_bp.get("/r/<string:shortcode>")
def resolve_shortcode(shortcode):
    url = Url.get_or_none(
        (Url.shortcode == shortcode) & (Url.is_active == True)
    )

    if url is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Short URL not found"
            }
        }), 404

    return redirect(url.original_url, code=302)