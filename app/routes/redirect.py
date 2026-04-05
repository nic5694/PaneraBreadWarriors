from flask import Blueprint, jsonify, redirect
from app.services import UrlService

redirect_bp = Blueprint("redirect", __name__)
url_service = UrlService()


@redirect_bp.route("/<string:shortcode>", methods=["GET"])
def resolve_shortcode(shortcode):
    """Resolve a shortcode and redirect to the original URL."""
    original_url = url_service.resolve_shortcode(shortcode)
    if not original_url:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Shortcode not found"}}), 404
    return redirect(original_url, code=302)
