from flask import Blueprint, jsonify, request, redirect
from app.services import UrlService, UrlConflictError

urls_bp = Blueprint("urls", __name__)
url_service = UrlService()

# Matches POST /urls
@urls_bp.post("/urls")
def create_url():
    data = request.get_json(silent=True) or {}
    try:
        url = url_service.create_url(data)
        return jsonify(url), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except UrlConflictError as exc:
        return jsonify({"error": str(exc)}), 409

# Matches GET /urls (with optional filters)
@urls_bp.get("/urls")
def list_urls():
    user_id = request.args.get("user_id") or request.get_json(silent=True, default={}).get("user_id")
    is_active = request.args.get("is_active")
    
    urls = url_service.list_urls(user_id=user_id, is_active=is_active)
    return jsonify(urls), 200

# Matches GET /urls/<id>, PUT /urls/<id>, DELETE /urls/<id>
@urls_bp.route("/urls/<int:url_id>", methods=["GET", "PUT", "DELETE"])
def handle_url_item(url_id):
    if request.method == "GET":
        url = url_service.get_url_by_id(url_id)
        return (jsonify(url), 200) if url else (jsonify({"error": "Not Found"}), 404)

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        url = url_service.update_url(url_id, data)
        return (jsonify(url), 200) if url else (jsonify({"error": "Not Found"}), 404)

    if request.method == "DELETE":
        url_service.delete_url(url_id)
        return "", 204

# Keep the redirect logic
@urls_bp.get("/r/<string:shortcode>")
def resolve_shortcode(shortcode):
    target_url = url_service.resolve_shortcode(shortcode)
    return redirect(target_url, code=302) if target_url else (jsonify({"error": "Not Found"}), 404)