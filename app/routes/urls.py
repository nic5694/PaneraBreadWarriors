from flask import Blueprint, jsonify, request, redirect

from app.services import UrlService, UrlConflictError

urls_bp = Blueprint("urls", __name__)


url_service = UrlService()


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

    try:
        url = url_service.create_url(data)
    except ValueError as exc:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc)
            }
        }), 400
    except UrlConflictError as exc:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": str(exc)
            }
        }), 409

    return jsonify({"data": url}), 201


@urls_bp.get("/r/<string:shortcode>")
def resolve_shortcode(shortcode):
    target_url = url_service.resolve_shortcode(shortcode)
    if target_url is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Short URL not found"
            }
        }), 404

    return redirect(target_url, code=302)