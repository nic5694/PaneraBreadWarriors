from flask import Blueprint, jsonify, request

from app.services import UserService, UserConflictError

users_bp = Blueprint("users", __name__, url_prefix="/users/v1/api/users")


user_service = UserService()


@users_bp.get("/")
def list_users():
    return jsonify({"data": user_service.list_users()}), 200


@users_bp.get("/<int:user_id>")
def get_user(user_id):
    user = user_service.get_user(user_id)
    if user is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "User not found"
            }
        }), 404

    return jsonify({"data": user}), 200


@users_bp.post("/")
def create_user():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Request body must be valid JSON"
            }
        }), 400

    try:
        user = user_service.create_user(data)
    except ValueError as exc:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc)
            }
        }), 400
    except UserConflictError as exc:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": str(exc)
            }
        }), 409

    return jsonify({"data": user}), 201


@users_bp.patch("/<int:user_id>")
def update_user(user_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Request body must be valid JSON"
            }
        }), 400

    try:
        user = user_service.update_user(user_id, data)
    except ValueError as exc:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc)
            }
        }), 400
    except UserConflictError as exc:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": str(exc)
            }
        }), 409

    if user is None:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "User not found"
            }
        }), 404

    return jsonify({"data": user}), 200


@users_bp.delete("/<int:user_id>")
def delete_user(user_id):
    if not user_service.delete_user(user_id):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "User not found"
            }
        }), 404

    return jsonify({
        "message": "User deleted successfully"
    }), 200